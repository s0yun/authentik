package web

import (
	"context"
	"errors"
	"net"
	"net/http"

	sentryhttp "github.com/getsentry/sentry-go/http"
	"github.com/gorilla/handlers"
	"github.com/gorilla/mux"
	"github.com/pires/go-proxyproto"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/gounicorn"
	"goauthentik.io/internal/outpost/proxyv2"
	"goauthentik.io/internal/utils/web"
	"goauthentik.io/internal/web/tenant_tls"
)

type WebServer struct {
	Bind    string
	BindTLS bool

	stop chan struct{} // channel for waiting shutdown

	ProxyServer *proxyv2.ProxyServer
	TenantTLS   *tenant_tls.Watcher

	m   *mux.Router
	lh  *mux.Router
	log *log.Entry
	p   *gounicorn.GoUnicorn
}

func NewWebServer(g *gounicorn.GoUnicorn) *WebServer {
	l := log.WithField("logger", "authentik.router")
	mainHandler := mux.NewRouter()
	mainHandler.Use(sentryhttp.New(sentryhttp.Options{}).Handle)
	mainHandler.Use(handlers.ProxyHeaders)
	mainHandler.Use(handlers.CompressHandler)
	logginRouter := mainHandler.NewRoute().Subrouter()
	logginRouter.Use(web.NewLoggingHandler(l, nil))

	ws := &WebServer{
		m:   mainHandler,
		lh:  logginRouter,
		log: l,
		p:   g,
	}
	ws.configureStatic()
	ws.configureRoutes()
	ws.configureProxy()
	return ws
}

func (ws *WebServer) configureRoutes() {
	ws.m.Path("/api/v3/sentry/").HandlerFunc(ws.APISentryProxy)
}

func (ws *WebServer) Start() {
	go ws.listenPlain()
	go ws.listenTLS()
}

func (ws *WebServer) Shutdown() {
	ws.stop <- struct{}{}
}

func (ws *WebServer) listenPlain() {
	ln, err := net.Listen("tcp", config.Get().Web.Listen)
	if err != nil {
		ws.log.WithError(err).Fatal("failed to listen")
	}
	proxyListener := &proxyproto.Listener{Listener: ln}
	defer proxyListener.Close()

	ws.log.WithField("listen", config.Get().Web.Listen).Info("Starting HTTP server")
	ws.serve(proxyListener)
	ws.log.WithField("listen", config.Get().Web.Listen).Info("Stopping HTTP server")
}

func (ws *WebServer) serve(listener net.Listener) {
	srv := &http.Server{
		Handler: ws.m,
	}

	// See https://golang.org/pkg/net/http/#Server.Shutdown
	idleConnsClosed := make(chan struct{})
	go func() {
		<-ws.stop // wait notification for stopping server

		// We received an interrupt signal, shut down.
		if err := srv.Shutdown(context.Background()); err != nil {
			// Error from closing listeners, or context timeout:
			ws.log.WithError(err).Warning("HTTP server Shutdown")
		}
		close(idleConnsClosed)
	}()

	err := srv.Serve(listener)
	if err != nil && !errors.Is(err, http.ErrServerClosed) {
		ws.log.WithError(err).Error("ERROR: http.Serve()")
	}
	<-idleConnsClosed
}
