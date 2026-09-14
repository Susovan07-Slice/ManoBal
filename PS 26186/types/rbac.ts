export type UserRole = 'commander' | 'welfare_officer';

export interface RoleConfig {
  role: UserRole;
  label: string;
  canViewFullExplanation: boolean;   // welfare_officer only
  canViewServiceIdentity: boolean;   // welfare_officer only
  canEditStatus: boolean;            // both, but scoped differently
}
