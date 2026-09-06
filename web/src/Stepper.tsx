export function Stepper({
  value,
  min = 0,
  onChange,
}: {
  value: number;
  min?: number;
  onChange: (next: number) => void;
}) {
  return (
    <span className="stepper">
      <button type="button" className="choice" onClick={() => onChange(Math.max(min, value - 1))}>
        −
      </button>
      <span>{value}</span>
      <button type="button" className="choice" onClick={() => onChange(value + 1)}>
        +
      </button>
    </span>
  );
}
