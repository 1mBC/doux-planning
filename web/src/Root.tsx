import { useEffect, useState } from "react";
import App from "./App";
import { clearToken, isEmployeeAffiliated, loadMe, readStoredToken, type Me } from "./auth";
import { ApiHttpError } from "./sandbox";
import { EmployeeLinkScreen, ImpersonateScreen, LoginScreen, parseImpersonatePath, RegisterScreen, SessionChrome, go } from "./AuthScreens";
import { ContextWizard } from "./ContextWizard";
import { EmployeePlanning } from "./EmployeePlanning";
import { AdminDenied, AdminPage, AdminPlanningPage, parseAdminPlanningPath } from "./AdminPage";
import { BenchPage } from "./BenchPage";
import { BenchStatsPage } from "./BenchStatsPage";
import { BenchComparePage, parseBenchComparePath, parseBenchRunPath } from "./BenchComparePage";
import { PublishedPlanning } from "./PublishedPlanning";
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
    if (path === "/admin/bench/versions") {
      go("/admin/bench");
    }
  }, [path]);

  useEffect(() => {
    if (me?.kind === "employee" && me.employee_id == null && path === "/planning") {
      go("/");
    }
  }, [me, path]);

  useEffect(() => {
    if (parseImpersonatePath(currentPath())) {
      setReady(true);
      return;
    }
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
          if (!parseImpersonatePath(currentPath())) {
            go("/login");
          }
        } else {
          setBanner(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
        }
        setReady(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const impersonateToken = parseImpersonatePath(path);
  const adminPlanningId = parseAdminPlanningPath(path);
  const route =
    impersonateToken
      ? "impersonate"
      : path === "/register"
        ? "register"
        : path === "/exemple"
          ? "exemple"
          : path === "/admin" || path.startsWith("/admin/")
            ? me?.admin
              ? path === "/admin/bench" || path === "/admin/bench/versions"
                ? "admin-bench"
                : path === "/admin/bench/stats"
                  ? "admin-bench-stats"
                  : parseBenchRunPath(path)
                    ? "admin-bench-run"
                    : parseBenchComparePath(path)
                      ? "admin-bench-compare"
                      : adminPlanningId
                        ? "admin-planning"
                        : path === "/admin"
                          ? "admin"
                          : "admin-bench-compare"
              : "admin-denied"
            : path === "/context" && me?.kind === "company"
            ? "context"
            : path === "/planning" && me?.kind === "company"
              ? "planning"
              : path === "/planning" && me && isEmployeeAffiliated(me)
                ? "employee"
                : me?.kind === "employee" &&
                    me.employee_id == null &&
                    (path === "/planning" || path === "/" || path === "/login")
                  ? "link"
                  : path === "/context" || path === "/planning"
                  ? "exemple"
                  : me?.kind === "company" && (path === "/" || path === "/login")
                    ? "context"
                    : me && isEmployeeAffiliated(me) && (path === "/" || path === "/login")
                      ? "employee"
                      : me
                        ? "exemple"
                        : "login";
  const canEdit = me?.kind !== "employee";

  if (!ready && !impersonateToken) {
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
      {route === "impersonate" && impersonateToken ? (
        <ImpersonateScreen
          token={impersonateToken}
          onConsumed={(next) => {
            setMe(next);
            window.history.replaceState({}, "", "/planning");
            setPath("/planning");
          }}
        />
      ) : null}
      {route === "context" ? <ContextWizard /> : null}
      {route === "admin" ? <AdminPage /> : null}
      {route === "admin-planning" && adminPlanningId ? <AdminPlanningPage restaurantId={adminPlanningId} /> : null}
      {route === "admin-bench" ? <BenchPage /> : null}
      {route === "admin-bench-stats" ? <BenchStatsPage /> : null}
      {route === "admin-bench-run" ? <BenchComparePage params={null} runId={parseBenchRunPath(path)} /> : null}
      {route === "admin-bench-compare" ? <BenchComparePage params={parseBenchComparePath(path)} /> : null}
      {route === "admin-denied" ? <AdminDenied /> : null}
      {route === "planning" ? <PublishedPlanning /> : null}
      {route === "employee" ? <EmployeePlanning /> : null}
      {route === "link" ? <EmployeeLinkScreen onLinked={setMe} /> : null}
      {route === "exemple" ? <App canEdit={canEdit} /> : null}
    </>
  );
}
