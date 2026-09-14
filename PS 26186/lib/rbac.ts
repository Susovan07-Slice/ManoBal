import { UserRole, RoleConfig } from '@/types/rbac';

export const ROLE_CONFIG: Record<UserRole, RoleConfig> = {
  commander: {
    role: 'commander',
    label: 'Commander',
    canViewFullExplanation: false,
    canViewServiceIdentity: false,
    canEditStatus: true,
  },
  welfare_officer: {
    role: 'welfare_officer',
    label: 'Welfare Officer',
    canViewFullExplanation: true,
    canViewServiceIdentity: true,
    canEditStatus: true,
  }
};
