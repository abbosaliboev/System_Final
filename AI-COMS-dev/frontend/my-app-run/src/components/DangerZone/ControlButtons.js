
const DangerZoneControls = ({ onSave, onDelete }) => {
  return (
    <div className="dangerzone-controls mt-2">
      <button className="dz-btn dz-save" onClick={onSave}>
        💾 Save Zones
      </button>
      <button className="dz-btn dz-delete" onClick={onDelete}>
        🗑 Delete All
      </button>
    </div>
  );
};

export default DangerZoneControls;
