import { STATUS_EXAME_BADGE_CLASSNAME, STATUS_EXAME_LABELS, StatusExame } from "../types/exame";

export default function StatusExameBadge({ status }: { status: StatusExame }) {
  return (
    <span className={`mg-badge ${STATUS_EXAME_BADGE_CLASSNAME[status]}`}>
      {STATUS_EXAME_LABELS[status]}
    </span>
  );
}
