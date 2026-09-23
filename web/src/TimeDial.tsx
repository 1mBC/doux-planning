import { useEffect, useMemo, useState } from "react";

export const TIME_DIAL_ARRIVAL_PRESET = 11 * 60;
export const TIME_DIAL_DEPARTURE_PRESET = 16 * 60;

const HOURS = Array.from({ length: 24 }, (_, hour) => hour);
const MINUTE_BUTTONS = [0, 15, 30, 45];

export function parseDialInt(raw: string, min: number, max: number): number | null {
  const trimmed = raw.trim();
  if (!/^\d+$/.test(trimmed)) {
    return null;
  }
  const value = Number(trimmed);
  if (!Number.isInteger(value) || value < min || value > max) {
    return null;
  }
  return value;
}

export function minutesToDialParts(timeMinutes: number): { hour: number; minute: number } {
  const wrapped = ((timeMinutes % 1440) + 1440) % 1440;
  return { hour: Math.floor(wrapped / 60), minute: wrapped % 60 };
}

export function composeTimeMinutes(previous: number, hour: number, minute: number): number {
  const dial = hour * 60 + minute;
  if (previous >= 1440) {
    return Math.floor(previous / 1440) * 1440 + dial;
  }
  return dial;
}

export function TimeDial({
  title,
  initialMinutes,
  onCancel,
  onConfirm,
}: {
  title: string;
  initialMinutes: number;
  onCancel: () => void;
  onConfirm: (hour: number, minute: number) => void;
}) {
  const parts = minutesToDialParts(initialMinutes);
  const [hourRaw, setHourRaw] = useState(String(parts.hour));
  const [minuteRaw, setMinuteRaw] = useState(String(parts.minute).padStart(2, "0"));
  const hour = useMemo(() => parseDialInt(hourRaw, 0, 23), [hourRaw]);
  const minute = useMemo(() => parseDialInt(minuteRaw, 0, 59), [minuteRaw]);
  const valid = hour !== null && minute !== null;

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        onCancel();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onCancel]);

  return (
    <div className="overlay-backdrop" role="presentation" onClick={onCancel}>
      <div
        className="overlay time-dial-overlay"
        role="dialog"
        aria-modal="true"
        aria-labelledby="time-dial-title"
        onClick={(event) => event.stopPropagation()}
      >
        <h3 id="time-dial-title">{title}</h3>
        <div className="time-dial-columns">
          <fieldset className="time-dial-panel">
            <legend>Heure</legend>
            <div className="time-dial-hours">
              {HOURS.map((value) => (
                <button
                  key={value}
                  type="button"
                  className={hour === value ? "choice active" : "choice"}
                  onClick={() => setHourRaw(String(value))}
                >
                  {value}
                </button>
              ))}
            </div>
            <label className="time-dial-input">
              Saisie
              <input
                inputMode="numeric"
                autoComplete="off"
                value={hourRaw}
                onChange={(event) => setHourRaw(event.target.value)}
                aria-label="Heure (0 à 23)"
              />
            </label>
          </fieldset>
          <fieldset className="time-dial-panel">
            <legend>Minutes</legend>
            <div className="time-dial-minutes">
              {MINUTE_BUTTONS.map((value) => (
                <button
                  key={value}
                  type="button"
                  className={minute === value ? "choice active" : "choice"}
                  onClick={() => setMinuteRaw(String(value).padStart(2, "0"))}
                >
                  {String(value).padStart(2, "0")}
                </button>
              ))}
            </div>
            <label className="time-dial-input">
              Saisie
              <input
                inputMode="numeric"
                autoComplete="off"
                value={minuteRaw}
                onChange={(event) => setMinuteRaw(event.target.value)}
                aria-label="Minutes (0 à 59)"
              />
            </label>
          </fieldset>
        </div>
        <div className="auth-row">
          <button type="button" className="choice" onClick={onCancel}>
            Annuler
          </button>
          <button
            type="button"
            className="choice active"
            disabled={!valid}
            onClick={() => {
              if (hour === null || minute === null) {
                return;
              }
              onConfirm(hour, minute);
            }}
          >
            Valider
          </button>
        </div>
      </div>
    </div>
  );
}
