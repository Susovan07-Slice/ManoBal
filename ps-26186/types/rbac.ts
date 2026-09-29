export type UserRole = 'admin' | 'officer' | 'welfare' | 'personnel';

export interface RoleConfig {
  role: UserRole;
  label: string;
  canViewFullExplanation: boolean;
  canViewServiceIdentity: boolean;
  canEditStatus: boolean;
  canManagePersonnel: boolean;
  canAccessAnalytics: boolean;
}
