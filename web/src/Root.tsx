import { useEffect, useState } from "react";
import App from "./App";
import { clearToken, loadMe, readStoredToken, type Me } from "./auth";
import { ApiHttpError } from "./sandbox";
import { LoginScreen, RegisterScreen, SessionChrome, go } from "./AuthScreens";
import "./App.css";

function currentPath(): string {
  return window.location.pathname;
}

export default function Root() {
  const [path, setPath] = useState(currentPath);
  const [me, setMe] = useState<Me | null>(null);
  const [ready, setReady] = useState(false);
  const [banner, setBanner] = useState<string | null>(null);

  useEffect(() => {
    function onPop() {
      setPath(currentPath());
    }
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  useEffect(() => {
    const token = readStoredToken();
    if (!token) {
      setReady(true);
      return;
    }
    let cancelled = false;
    loadMe()
      .then((next) => {
        if (!cancelled) {
          setMe(next);
          setReady(true);
        }
      })
      .catch((err: unknown) => {
        if (cancelled) {
          return;
        }
        if (err instanceof ApiHttpError && err.status === 401) {
          clearToken();
          setMe(null);
          go("/login");
        } else {
          setBanner(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
        }
        setReady(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const route = path === "/register" ? "register" : path === "/exemple" || (me && path !== "/register") ? "exemple" : "login";
  const canEdit = me?.kind !== "employee";

  if (!ready) {
    return (
      <main className="page">
        <SessionChrome me={me} onSignedOut={() => setMe(null)} />
        <p className="sub">Chargement de la session…</p>
      </main>
    );
  }

  return (
    <>
      <SessionChrome me={me} onSignedOut={() => setMe(null)} />
      {banner ? (
        <p className="error" role="alert">
          {banner}
        </p>
      ) : null}
      {route === "login" ? <LoginScreen onSignedIn={setMe} /> : null}
      {route === "register" ? <RegisterScreen onSignedIn={setMe} /> : null}
      {route === "exemple" ? <App canEdit={canEdit} /> : null}
    </>
  );
}
