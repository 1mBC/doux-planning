export function Stepper({
  value,
  min,
  step = 1,
  display,
  label,
  disabled,
  onChange,
}: {
  value: number;
  min?: number;
  step?: number;
  display?: string;
  label?: string;
  disabled?: boolean;
  onChange: (next: number) => void;
}) {
  const atMin = min !== undefined && value <= min;
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
        <span className="stepper-value">{display ?? value}</span>
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
