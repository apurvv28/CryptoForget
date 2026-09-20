export default function SourceToggle({ value, onChange }) {
  return (
    <div className="cf-segmented" role="group" aria-label="News source">
      <button
        type="button"
        aria-pressed={value === 'live'}
        onClick={() => onChange('live')}
        title="Fresh headlines fetched by the backend from Google News RSS"
      >
        Live news
      </button>
      <button
        type="button"
        aria-pressed={value === 'mind'}
        onClick={() => onChange('mind')}
        title="The MIND-small dataset the recommendation model was built on"
      >
        MIND catalog
      </button>
    </div>
  );
}