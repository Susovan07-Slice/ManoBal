import { UserRole, RoleConfig } from '@/types/rbac';

export const ROLE_CONFIG: Record<UserRole, RoleConfig> = {
  admin: {
    role: 'admin',
    label: 'System Administrator',
    canViewFullExplanation: true,
    canViewServiceIdentity: true,
    canEditStatus: true,
    canManagePersonnel: true,
    canAccessAnalytics: true,
  },
  officer: {
    role: 'officer',
    label: 'Commanding Officer',
    canViewFullExplanation: true,
    canViewServiceIdentity: true,
    canEditStatus: true,
    canManagePersonnel: true,
    canAccessAnalytics: true,
  },
  welfare: {
    role: 'welfare',
    label: 'Welfare Officer / Counselor',
    canViewFullExplanation: true,
    canViewServiceIdentity: true,
    canEditStatus: true,
    canManagePersonnel: false,
    canAccessAnalytics: true,
  },
  personnel: {
    role: 'personnel',
    label: 'Personnel / Jawan',
    canViewFullExplanation: false,
    canViewServiceIdentity: false,
    canEditStatus: false,
    canManagePersonnel: false,
    canAccessAnalytics: false,
  },
};
