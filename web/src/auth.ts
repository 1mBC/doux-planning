import { isRecord, PayloadError, requireArray, requireRecord, requireString } from "./api";
import { ApiHttpError } from "./sandbox";

export const AUTH_TOKEN_KEY = "doux.auth.token";

export type AccountKind = "company" | "employee";

export type Me = {
  kind: AccountKind;
  email: string;
  restaurant_id: string;
  employee_id: string | null;
};

export type AuthSession = {
  token: string;
  me: Me;
};

export type InviteEmployee = {
  id: string;
  name: string;
  role: string;
  team: "salle" | "cuisine";
};

export type InvitePreview = {
  restaurant_name: string;
  employees: InviteEmployee[];
};

export type RegisterBody = {
  kind: AccountKind;
  email: string;
  password: string;
  company_code?: string;
  employee_token?: string;
  employee_id?: string;
};

async function parseDetail(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();
    if (isRecord(body) && typeof body.detail === "string") {
      return body.detail;
    }
  } catch {
    /* ignore */
  }
  return `HTTP ${response.status}`;
}

function authHeaders(withBearer: boolean, json: boolean): HeadersInit {
  const headers: Record<string, string> = {};
  if (json) {
    headers["Content-Type"] = "application/json";
  }
  if (withBearer) {
    const token = sessionStorage.getItem(AUTH_TOKEN_KEY);
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
  }
  return headers;
}

async function sendAuth(url: string, init: RequestInit, withBearer: boolean): Promise<unknown> {
  const headers = new Headers(init.headers);
  const extra = authHeaders(withBearer, headers.get("Content-Type") === "application/json" || Boolean(init.body));
  for (const [key, value] of Object.entries(extra)) {
    headers.set(key, value);
  }
  const response = await fetch(url, { ...init, headers });
  if (response.status === 204) {
    return null;
  }
  if (!response.ok) {
    throw new ApiHttpError(response.status, await parseDetail(response));
  }
  return response.json();
}

function parseKind(value: unknown, path: string): AccountKind {
  if (value === "company" || value === "employee") {
    return value;
  }
  throw new PayloadError(`kind inattendu : ${path}`);
}

function parseNullableEmployeeId(value: unknown, path: string): string | null {
  if (value === null) {
    return null;
  }
  if (typeof value !== "string") {
    throw new PayloadError(`clé invalide : ${path}`);
  }
  return value;
}

export function parseMe(value: unknown): Me {
  if (!isRecord(value)) {
    throw new PayloadError("réponse me invalide");
  }
  if (!("employee_id" in value)) {
    throw new PayloadError("clé absente : me.employee_id");
  }
  return {
    kind: parseKind(value.kind, "me.kind"),
    email: requireString(value, "email", "me"),
    restaurant_id: requireString(value, "restaurant_id", "me"),
    employee_id: parseNullableEmployeeId(value.employee_id, "me.employee_id"),
  };
}

export function parseAuthSession(value: unknown): AuthSession {
  if (!isRecord(value)) {
    throw new PayloadError("réponse session invalide");
  }
  return {
    token: requireString(value, "token", "session"),
    me: parseMe(requireRecord(value, "me", "session")),
  };
}

function parseTeam(value: unknown, path: string): "salle" | "cuisine" {
  if (value === "salle" || value === "cuisine") {
    return value;
  }
  throw new PayloadError(`team inattendue : ${path}`);
}

function parseInviteEmployee(value: unknown, path: string): InviteEmployee {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  return {
    id: requireString(value, "id", path),
    name: requireString(value, "name", path),
    role: requireString(value, "role", path),
    team: parseTeam(value.team, `${path}.team`),
  };
}

export function parseInvitePreview(value: unknown): InvitePreview {
  if (!isRecord(value)) {
    throw new PayloadError("réponse invites invalide");
  }
  return {
    restaurant_name: requireString(value, "restaurant_name", "invites"),
    employees: requireArray(value, "employees", "invites").map((item, i) =>
      parseInviteEmployee(item, `invites.employees[${i}]`),
    ),
  };
}

export function readStoredToken(): string | null {
  return sessionStorage.getItem(AUTH_TOKEN_KEY);
}

export function storeToken(token: string): void {
  sessionStorage.setItem(AUTH_TOKEN_KEY, token);
}

export function clearToken(): void {
  sessionStorage.removeItem(AUTH_TOKEN_KEY);
}

export function persistSession(session: AuthSession): Me {
  storeToken(session.token);
  return session.me;
}

export async function login(email: string, password: string): Promise<Me> {
  return persistSession(parseAuthSession(await sendAuth("/v1/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  }, true)));
}

export async function register(body: RegisterBody): Promise<Me> {
  return persistSession(parseAuthSession(await sendAuth("/v1/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }, true)));
}

export async function loadMe(): Promise<Me> {
  return parseMe(await sendAuth("/v1/me", { method: "GET" }, true));
}

export async function logout(): Promise<void> {
  try {
    await sendAuth("/v1/auth/logout", { method: "POST" }, true);
  } finally {
    clearToken();
  }
}

export async function loadInvites(companyCode: string): Promise<InvitePreview> {
  const encoded = encodeURIComponent(companyCode);
  return parseInvitePreview(await sendAuth(`/v1/invites/${encoded}`, { method: "GET" }, false));
}

export function kindLabel(kind: AccountKind): string {
  return kind === "company" ? "Entreprise" : "Salarié";
}
