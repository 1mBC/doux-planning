import { useEffect, useRef, useState } from "react";
import { ApiHttpError, previewFill, previewSandbox } from "./sandbox";
import { employeeName, HoursImpact, SwapReplaceImpact } from "./impact";
import { dayThenClock, formatClock, GESTURE_CHOICE_FR } from "./format";
import type { Employee, FillSlot, Gesture, PreviewProposal, ShiftIdentity } from "./types";

const STEP_MINUTES = 15;

function proposalTitle(proposal: PreviewProposal, employees: Employee[]): string {
  if (proposal.gesture === "replace" || proposal.gesture === "fill") {
    return employeeName(employees, proposal.employee_id);
  }
  if (proposal.partner) {
    return `${dayThenClock(proposal.partner.day_index, proposal.partner.start_minutes, proposal.partner.end_minutes)} · ${employeeName(employees, proposal.partner.employee_id)}`;
  }
  return `Proposition ${proposal.rank}`;
}

export function Overlay({
  shift,
  employees,
  onClose,
  onCommit,
  onError,
}: {
  shift: ShiftIdentity;
  employees: Employee[];
  onClose: () => void;
  onCommit: (gesture: Gesture, proposal: PreviewProposal) => Promise<void>;
  onError: (message: string) => void;
}) {
  const [gesture, setGesture] = useState<Gesture | null>(null);
  const [loading, setLoading] = useState(false);
  const [proposals, setProposals] = useState<PreviewProposal[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [startMinutes, setStartMinutes] = useState(shift.start_minutes);
  const [endMinutes, setEndMinutes] = useState(shift.end_minutes);
  const previewSeq = useRef(0);

  async function chooseGesture(next: Gesture) {
    previewSeq.current += 1;
    setGesture(next);
    setLocalError(null);
    setProposals(null);
    if (next === "retune") {
      setStartMinutes(shift.start_minutes);
      setEndMinutes(shift.end_minutes);
      return;
    }
    setLoading(true);
    try {
      setProposals(await previewSandbox(next, shift));
    } catch (err) {
      const message = err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue";
      setLocalError(message);
      onError(message);
    } finally {
      setLoading(false);
    }
  }

  async function stepHours(which: "start" | "end", delta: number) {
    const nextStart = which === "start" ? startMinutes + delta : startMinutes;
    const nextEnd = which === "end" ? endMinutes + delta : endMinutes;
    setStartMinutes(nextStart);
    setEndMinutes(nextEnd);
    const seq = ++previewSeq.current;
    setLoading(true);
    setLocalError(null);
    try {
      const next = await previewSandbox("retune", shift, { start_minutes: nextStart, end_minutes: nextEnd });
      if (seq !== previewSeq.current) {
        return;
      }
      setProposals(next);
    } catch (err) {
      if (seq !== previewSeq.current) {
        return;
      }
      setProposals(null);
      setLocalError(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
    } finally {
      if (seq === previewSeq.current) {
        setLoading(false);
      }
    }
  }

  const retuneProposal = gesture === "retune" && proposals && proposals.length > 0 ? proposals[0] : null;

  return (
    <div className="overlay-backdrop" role="presentation" onClick={onClose}>
      <div
        className="overlay"
        role="dialog"
        aria-modal="true"
        aria-labelledby="overlay-title"
        onClick={(event) => event.stopPropagation()}
      >
        <h2 id="overlay-title">Modifier le créneau</h2>
        <p className="sub">
          {employeeName(employees, shift.employee_id)} · {formatClock(shift.start_minutes)} –{" "}
          {formatClock(shift.end_minutes)}
        </p>
        <div className="gestures">
          {GESTURE_CHOICE_FR.map((item) => (
            <button
              key={item.id}
              type="button"
              className={gesture === item.id ? "choice active" : "choice"}
              onClick={() => void chooseGesture(item.id)}
            >
              {item.label}
            </button>
          ))}
        </div>
        {gesture === "retune" ? (
          <div className="steppers">
            <div className="stepper">
              <span>Début</span>
              <button type="button" className="choice" disabled={loading || busy} onClick={() => void stepHours("start", -STEP_MINUTES)}>
                −
              </button>
              <strong>{formatClock(startMinutes)}</strong>
              <button type="button" className="choice" disabled={loading || busy} onClick={() => void stepHours("start", STEP_MINUTES)}>
                +
              </button>
            </div>
            <div className="stepper">
              <span>Fin</span>
              <button type="button" className="choice" disabled={loading || busy} onClick={() => void stepHours("end", -STEP_MINUTES)}>
                −
              </button>
              <strong>{formatClock(endMinutes)}</strong>
              <button type="button" className="choice" disabled={loading || busy} onClick={() => void stepHours("end", STEP_MINUTES)}>
                +
              </button>
            </div>
          </div>
        ) : null}
        {loading ? <p className="sub">Chargement des propositions…</p> : null}
        {localError ? (
          <p className="error" role="alert">
            {localError}
          </p>
        ) : null}
        {gesture === "retune" && retuneProposal && !loading ? (
          <div className="retune-preview">
            <HoursImpact impact={retuneProposal.impact} employees={employees} />
            <button
              type="button"
              className="choice active"
              disabled={busy}
              onClick={() => {
                setBusy(true);
                void onCommit("retune", retuneProposal).finally(() => setBusy(false));
              }}
            >
              Valider
            </button>
          </div>
        ) : null}
        {gesture === "retune" && proposals && proposals.length === 0 && !loading && !localError ? (
          <p className="sub">Aucune proposition du moteur.</p>
        ) : null}
        {gesture && gesture !== "retune" && proposals && !loading ? (
          <ol className="proposals">
            {proposals.length === 0 ? (
              <li className="sub">Aucune proposition du moteur.</li>
            ) : (
              proposals.map((proposal) => (
                <li key={`${proposal.gesture}-${proposal.rank}`}>
                  <button
                    type="button"
                    className="proposal"
                    disabled={busy}
                    onClick={() => {
                      setBusy(true);
                      void onCommit(gesture, proposal).finally(() => setBusy(false));
                    }}
                  >
                    <strong>
                      #{proposal.rank} · {proposalTitle(proposal, employees)}
                    </strong>
                    <SwapReplaceImpact impact={proposal.impact} employees={employees} />
                  </button>
                </li>
              ))
            )}
          </ol>
        ) : null}
        <button type="button" className="choice" onClick={onClose}>
          Fermer
        </button>
      </div>
    </div>
  );
}

export function FillOverlay({
  slot,
  employees,
  onClose,
  onCommit,
  onError,
}: {
  slot: FillSlot;
  employees: Employee[];
  onClose: () => void;
  onCommit: (proposal: PreviewProposal) => Promise<void>;
  onError: (message: string) => void;
}) {
  const [loading, setLoading] = useState(true);
  const [proposals, setProposals] = useState<PreviewProposal[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [startMinutes, setStartMinutes] = useState<number | null>(null);
  const [endMinutes, setEndMinutes] = useState<number | null>(null);
  const previewSeq = useRef(0);

  useEffect(() => {
    const seq = ++previewSeq.current;
    setLoading(true);
    setLocalError(null);
    void previewFill(slot, { start_minutes: null, end_minutes: null })
      .then((next) => {
        if (seq !== previewSeq.current) {
          return;
        }
        setProposals(next);
        const first = next[0];
        if (first && first.start_minutes !== null && first.end_minutes !== null) {
          setStartMinutes(first.start_minutes);
          setEndMinutes(first.end_minutes);
        }
      })
      .catch((err: unknown) => {
        if (seq !== previewSeq.current) {
          return;
        }
        const message = err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue";
        setLocalError(message);
        onError(message);
      })
      .finally(() => {
        if (seq === previewSeq.current) {
          setLoading(false);
        }
      });
  }, [slot, onError]);

  async function stepHours(which: "start" | "end", delta: number) {
    if (startMinutes === null || endMinutes === null) {
      return;
    }
    const nextStart = which === "start" ? startMinutes + delta : startMinutes;
    const nextEnd = which === "end" ? endMinutes + delta : endMinutes;
    setStartMinutes(nextStart);
    setEndMinutes(nextEnd);
    const seq = ++previewSeq.current;
    setLoading(true);
    setLocalError(null);
    try {
      const next = await previewFill(slot, { start_minutes: nextStart, end_minutes: nextEnd });
      if (seq !== previewSeq.current) {
        return;
      }
      setProposals(next);
    } catch (err) {
      if (seq !== previewSeq.current) {
        return;
      }
      setProposals(null);
      setLocalError(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
    } finally {
      if (seq === previewSeq.current) {
        setLoading(false);
      }
    }
  }

  const lineProposal = proposals?.find((item) => item.employee_id === slot.employee_id) ?? null;
  const others = (proposals ?? []).filter((item) => item.employee_id !== slot.employee_id);
  const start = startMinutes;
  const end = endMinutes;
  const canCommit = (proposal: PreviewProposal) =>
    proposal.start_minutes !== null && proposal.end_minutes !== null && !busy && !loading;

  return (
    <div className="overlay-backdrop" role="presentation" onClick={onClose}>
      <div
        className="overlay"
        role="dialog"
        aria-modal="true"
        aria-labelledby="overlay-title"
        onClick={(event) => event.stopPropagation()}
      >
        <h2 id="overlay-title">Poser un créneau</h2>
        <p className="sub">
          {employeeName(employees, slot.employee_id)}
          {start !== null && end !== null ? ` · ${formatClock(start)} – ${formatClock(end)}` : ""}
        </p>
        {start !== null && end !== null ? (
          <div className="steppers">
            <div className="stepper">
              <span>Début</span>
              <button type="button" className="choice" disabled={loading || busy} onClick={() => void stepHours("start", -STEP_MINUTES)}>
                −
              </button>
              <strong>{formatClock(start)}</strong>
              <button type="button" className="choice" disabled={loading || busy} onClick={() => void stepHours("start", STEP_MINUTES)}>
                +
              </button>
            </div>
            <div className="stepper">
              <span>Fin</span>
              <button type="button" className="choice" disabled={loading || busy} onClick={() => void stepHours("end", -STEP_MINUTES)}>
                −
              </button>
              <strong>{formatClock(end)}</strong>
              <button type="button" className="choice" disabled={loading || busy} onClick={() => void stepHours("end", STEP_MINUTES)}>
                +
              </button>
            </div>
          </div>
        ) : null}
        {loading ? <p className="sub">Chargement des propositions…</p> : null}
        {localError ? (
          <p className="error" role="alert">
            {localError}
          </p>
        ) : null}
        {lineProposal && !loading ? (
          <div className="retune-preview">
            <strong>{employeeName(employees, lineProposal.employee_id)}</strong>
            <SwapReplaceImpact impact={lineProposal.impact} employees={employees} />
            <button
              type="button"
              className="choice active"
              disabled={!canCommit(lineProposal)}
              onClick={() => {
                setBusy(true);
                void onCommit(lineProposal).finally(() => setBusy(false));
              }}
            >
              Valider
            </button>
          </div>
        ) : null}
        {others.length > 0 && !loading ? (
          <ol className="proposals">
            {others.map((proposal) => (
              <li key={`${proposal.gesture}-${proposal.rank}`}>
                <button
                  type="button"
                  className="proposal"
                  disabled={!canCommit(proposal)}
                  onClick={() => {
                    setBusy(true);
                    void onCommit(proposal).finally(() => setBusy(false));
                  }}
                >
                  <strong>
                    #{proposal.rank} · {proposalTitle(proposal, employees)}
                  </strong>
                  <SwapReplaceImpact impact={proposal.impact} employees={employees} />
                </button>
              </li>
            ))}
          </ol>
        ) : null}
        {proposals && proposals.length === 0 && !loading && !localError ? (
          <p className="sub">Aucune proposition du moteur.</p>
        ) : null}
        <button type="button" className="choice" onClick={onClose}>
          Fermer
        </button>
      </div>
    </div>
  );
}
