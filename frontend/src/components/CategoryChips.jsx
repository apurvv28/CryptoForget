export default function CategoryChips({ options, value, onChange }) {
  return (
    <div className="cf-chiprow" role="group" aria-label="Categories">
      {options.map((o) => (
        <button
          key={o.id}
          type="button"
          className="cf-pill"
          aria-pressed={value === o.id}
          onClick={() => onChange(o.id)}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}