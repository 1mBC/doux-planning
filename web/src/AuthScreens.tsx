import { useMemo, useState, type FormEvent } from "react";
import { ApiHttpError } from "./sandbox";
import {
  kindLabel,
  loadInvites,
  login,
  logout,
  register,
  type InviteEmployee,
  type Me,
} from "./auth";
import { UI_RELEASE } from "./release";

export function go(path: string): void {
  window.history.pushState({}, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

export function SessionChrome({
  me,
  onSignedOut,
}: {
  me: Me | null;
  onSignedOut: () => void;
}) {
  const [busy, setBusy] = useState(false);

  async function signOut() {
    setBusy(true);
    try {
      await logout();
    } catch {
      /* token already forgotten in logout() */
    } finally {
      setBusy(false);
      onSignedOut();
      go("/login");
    }
  }

  return (
    <div className="session-bar">
      <nav className="session-links">
        {me ? (
          <>
            <span>
              {me.email} · {kindLabel(me.kind)}
            </span>
            <button type="button" className="choice" disabled={busy} onClick={() => void signOut()}>
              {busy ? "Déconnexion…" : "Déconnexion"}
            </button>
            {me.kind === "company" ? (
              <>
                <button type="button" className="choice" onClick={() => go("/context")}>
                  Mon restaurant
                </button>
                <button type="button" className="choice" onClick={() => go("/planning")}>
                  Planning
                </button>
              </>
            ) : null}
          </>
        ) : (
          <>
            <button type="button" className="choice" onClick={() => go("/login")}>
              Connexion
            </button>
            <button type="button" className="choice" onClick={() => go("/register")}>
              Inscription
            </button>
          </>
        )}
        <button type="button" className="choice" onClick={() => go("/exemple")}>
          Voir l’exemple
        </button>
      </nav>
      <p className="release">
        v{UI_RELEASE.version} · {UI_RELEASE.note}
      </p>
    </div>
  );
}

export function LoginScreen({ onSignedIn }: { onSignedIn: (me: Me) => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (password.length < 8) {
      setError("Le mot de passe doit contenir au moins 8 caractères.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const me = await login(email, password);
      onSignedIn(me);
      go(me.kind === "company" ? "/context" : "/exemple");
    } catch (err) {
      setError(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="page auth-page">
      <h1>Connexion</h1>
      <p className="sub">Email et mot de passe. Le type de compte vient de la session.</p>
      <form className="auth-form" onSubmit={(event) => void submit(event)}>
        <label htmlFor="login-email">Email</label>
        <input
          id="login-email"
          type="email"
          autoComplete="username"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
        <label htmlFor="login-password">Mot de passe</label>
        <input
          id="login-password"
          type="password"
          autoComplete="current-password"
          required
          minLength={8}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        {error ? (
          <p className="error" role="alert">
            {error}
          </p>
        ) : null}
        <button type="submit" className="choice active" disabled={busy}>
          {busy ? "Connexion…" : "Se connecter"}
        </button>
      </form>
      <p className="sub">
        <button type="button" className="linkish" onClick={() => go("/register")}>
          Créer un compte
        </button>
        {" · "}
        <button type="button" className="linkish" onClick={() => go("/exemple")}>
          Voir l’exemple
        </button>
      </p>
    </main>
  );
}

export function RegisterScreen({ onSignedIn }: { onSignedIn: (me: Me) => void }) {
  const query = useMemo(() => new URLSearchParams(window.location.search), []);
  const qrCode = query.get("company_code");
  const qrToken = query.get("employee_token");
  const isQr = Boolean(qrCode && qrToken);

  const [kind, setKind] = useState<"company" | "employee">(isQr ? "employee" : "company");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [companyCode, setCompanyCode] = useState(qrCode ?? "");
  const [fiches, setFiches] = useState<InviteEmployee[] | null>(null);
  const [restaurantName, setRestaurantName] = useState("");
  const [employeeId, setEmployeeId] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function fetchFiches() {
    setBusy(true);
    setError(null);
    try {
      const preview = await loadInvites(companyCode.trim());
      setRestaurantName(preview.restaurant_name);
      setFiches(preview.employees);
      setEmployeeId(preview.employees[0]?.id ?? "");
    } catch (err) {
      setFiches(null);
      setError(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
    } finally {
      setBusy(false);
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (password.length < 8) {
      setError("Le mot de passe doit contenir au moins 8 caractères.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const me = isQr
        ? await register({
            kind: "employee",
            email,
            password,
            company_code: qrCode ?? "",
            employee_token: qrToken ?? "",
          })
        : kind === "company"
          ? await register({ kind: "company", email, password })
          : await register({
              kind: "employee",
              email,
              password,
              company_code: companyCode.trim(),
              employee_id: employeeId,
            });
      onSignedIn(me);
      go(me.kind === "company" ? "/context" : "/exemple");
    } catch (err) {
      setError(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="page auth-page">
      <h1>Inscription</h1>
      <p className="sub">
        {isQr
          ? "Lien QR : compte salarié, fiche déjà choisie."
          : "Entreprise (email + mot de passe) ou salarié (code puis fiche)."}
      </p>
      {!isQr ? (
        <div className="auth-switch">
          <button
            type="button"
            className={kind === "company" ? "choice active" : "choice"}
            onClick={() => setKind("company")}
          >
            Entreprise
          </button>
          <button
            type="button"
            className={kind === "employee" ? "choice active" : "choice"}
            onClick={() => setKind("employee")}
          >
            Salarié
          </button>
        </div>
      ) : null}
      <form className="auth-form" onSubmit={(event) => void submit(event)}>
        {kind === "employee" && !isQr ? (
          <>
            <label htmlFor="reg-code">Code entreprise</label>
            <div className="auth-row">
              <input
                id="reg-code"
                value={companyCode}
                onChange={(event) => setCompanyCode(event.target.value)}
                required
              />
              <button type="button" className="choice" disabled={busy || !companyCode.trim()} onClick={() => void fetchFiches()}>
                Charger les fiches
              </button>
            </div>
            {fiches ? (
              <>
                <p className="sub">{restaurantName ? restaurantName : "Entreprise sans nom pour l’instant."}</p>
                {fiches.length === 0 ? (
                  <p className="sub">Aucune fiche disponible.</p>
                ) : (
                  <fieldset className="auth-fiches">
                    <legend>Fiche</legend>
                    {fiches.map((person) => (
                      <label key={person.id} className="auth-fiche">
                        <input
                          type="radio"
                          name="fiche"
                          value={person.id}
                          checked={employeeId === person.id}
                          onChange={() => setEmployeeId(person.id)}
                        />
                        <span>
                          {person.name} · {person.role} · {person.team}
                        </span>
                      </label>
                    ))}
                  </fieldset>
                )}
              </>
            ) : null}
          </>
        ) : null}
        <label htmlFor="reg-email">Email</label>
        <input
          id="reg-email"
          type="email"
          autoComplete="username"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
        <label htmlFor="reg-password">Mot de passe</label>
        <input
          id="reg-password"
          type="password"
          autoComplete="new-password"
          required
          minLength={8}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        {error ? (
          <p className="error" role="alert">
            {error}
          </p>
        ) : null}
        <button
          type="submit"
          className="choice active"
          disabled={
            busy || (kind === "employee" && !isQr && (!employeeId || fiches === null))
          }
        >
          {busy ? "Inscription…" : "Créer le compte"}
        </button>
      </form>
      <p className="sub">
        <button type="button" className="linkish" onClick={() => go("/login")}>
          Connexion
        </button>
        {" · "}
        <button type="button" className="linkish" onClick={() => go("/exemple")}>
          Voir l’exemple
        </button>
      </p>
    </main>
  );
}
