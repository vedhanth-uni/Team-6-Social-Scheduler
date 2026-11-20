import type { FriendLevel } from '../api files/friendsApi';

const LEVEL_LABELS: Record<FriendLevel, string> = {
    close: 'Close',
    professional: 'Professional',
};

function LevelChip({ level }: { level: FriendLevel }) {
    return <span className={`level-chip level-chip--${level}`}>{LEVEL_LABELS[level]}</span>;
}

export default LevelChip;
