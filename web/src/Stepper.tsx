export function Stepper({
  value,
  min,
  step = 1,
  display,
  label,
  disabled,
  onChange,
  onDisplayClick,
}: {
  value: number;
  min?: number;
  step?: number;
  display?: string;
  label?: string;
  disabled?: boolean;
  onChange: (next: number) => void;
  onDisplayClick?: () => void;
}) {
  const atMin = min !== undefined && value <= min;
  const shown = display ?? value;
  return (
    <span className="stepper-frame">
      {label ? <span className="stepper-label">{label}</span> : null}
      <span className="stepper">
        <button
          type="button"
          className="stepper-btn"
          disabled={disabled || atMin}
          aria-label="Moins"
          onClick={() => onChange(min !== undefined ? Math.max(min, value - step) : value - step)}
        >
          −
        </button>
        {onDisplayClick ? (
          <button
            type="button"
            className="stepper-value stepper-clock"
            disabled={disabled}
            aria-label="Modifier l’heure"
            onClick={onDisplayClick}
          >
            {shown}
          </button>
        ) : (
          <span className="stepper-value">{shown}</span>
        )}
        <button
          type="button"
          className="stepper-btn"
          disabled={disabled}
          aria-label="Plus"
          onClick={() => onChange(value + step)}
        >
          +
        </button>
      </span>
    </span>
  );
}
