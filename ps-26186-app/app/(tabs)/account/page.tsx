"use client";

import React, { useState } from "react";
import { useAuth } from "@/lib/AuthContext";
import { changePassword, changeBattalion } from "@/lib/auth";
import { LogOut, Key, MapPin, ChevronRight, ShieldCheck, User as UserIcon, X } from "lucide-react";

export default function AccountRoute() {
  const { user, logout } = useAuth();
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordStatus, setPasswordStatus] = useState<{type: 'error' | 'success', msg: string} | null>(null);

  const [showBattalionModal, setShowBattalionModal] = useState(false);
  const [battalion, setBattalion] = useState(user?.battalion || "7th Battalion");
  const [location, setLocation] = useState(user?.location || "Srinagar");
  const [battalionStatus, setBattalionStatus] = useState<{type: 'error' | 'success', msg: string} | null>(null);

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordStatus(null);
    try {
      await changePassword(oldPassword, newPassword);
      setPasswordStatus({ type: 'success', msg: 'Password updated successfully!' });
      setTimeout(() => setShowPasswordModal(false), 2000);
    } catch (err: any) {
      setPasswordStatus({ type: 'error', msg: err.message || 'Failed to update password.' });
    }
  };

  const handleBattalionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBattalionStatus(null);
    try {
      await changeBattalion(battalion, location);
      setBattalionStatus({ type: 'success', msg: 'Battalion updated successfully! Please refresh.' });
      setTimeout(() => setShowBattalionModal(false), 2000);
    } catch (err: any) {
      setBattalionStatus({ type: 'error', msg: err.message || 'Failed to update battalion.' });
    }
  };

  return (
    <div className="p-4 flex flex-col gap-6 pb-44 min-w-0 animate-fade-up">
      {/* Header */}
      <div className="flex items-center gap-4 mb-2">
        <div className="w-16 h-16 rounded-full bg-white shadow-sm border border-sky-200 flex items-center justify-center overflow-hidden">
          {user?.role === "personnel" ? (
            <img src="/logo.png" alt="Profile" className="w-full h-full object-cover scale-110" />
          ) : (
            <UserIcon className="w-8 h-8 text-brand-500" />
          )}
        </div>
        <div>
          <h2 className="text-[22px] font-bold text-ink">{user?.username || "Account"}</h2>
          <p className="text-[13px] text-ink-3 mt-0.5 font-medium flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-ok" /> 
            {user?.role === "personnel" ? "Jawan / Personnel" : "Authorized User"}
          </p>
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="eyebrow">Account Settings</h3>

        <div className="bg-white rounded-[24px] shadow-[0_10px_30px_rgba(31,110,140,0.08)] border border-sky-100 overflow-hidden">
          
          {/* Change Password */}
          <button 
            className="w-full flex items-center justify-between p-5 border-b border-sky-50 hover:bg-sky-50/50 transition-colors"
            onClick={() => {
              setPasswordStatus(null);
              setOldPassword("");
              setNewPassword("");
              setShowPasswordModal(true);
            }}
          >
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-2xl bg-brand-50 flex items-center justify-center text-brand-500">
                <Key className="w-5 h-5" />
              </div>
              <div className="text-left">
                <p className="text-[15px] font-bold text-ink">Change Password</p>
                <p className="text-[12px] text-ink-3 font-medium mt-0.5">Update your security credentials</p>
              </div>
            </div>
            <ChevronRight className="w-5 h-5 text-ink-3" />
          </button>

          {/* Change Battalion */}
          <button 
            className="w-full flex items-center justify-between p-5 border-b border-sky-50 hover:bg-sky-50/50 transition-colors"
            onClick={() => {
              setBattalionStatus(null);
              setBattalion(user?.battalion || "7th Battalion");
              setLocation(user?.location || "Srinagar");
              setShowBattalionModal(true);
            }}
          >
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-2xl bg-brand-50 flex items-center justify-center text-brand-500">
                <MapPin className="w-5 h-5" />
              </div>
              <div className="text-left">
                <p className="text-[15px] font-bold text-ink">Change Battalion</p>
                <p className="text-[12px] text-ink-3 font-medium mt-0.5">Transfer unit or location assignment</p>
              </div>
            </div>
            <ChevronRight className="w-5 h-5 text-ink-3" />
          </button>

          {/* Logout */}
          <button 
            className="w-full flex items-center justify-between p-5 hover:bg-alert-bg/50 transition-colors"
            onClick={() => setShowLogoutConfirm(true)}
          >
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-2xl bg-alert-bg flex items-center justify-center text-alert">
                <LogOut className="w-5 h-5" />
              </div>
              <div className="text-left">
                <p className="text-[15px] font-bold text-alert">Log Out</p>
                <p className="text-[12px] text-alert/70 font-medium mt-0.5">Sign out of the ManoBal Portal</p>
              </div>
            </div>
            <ChevronRight className="w-5 h-5 text-alert/50" />
          </button>
        </div>
      </div>

      {/* Password Modal */}
      {showPasswordModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm px-6 animate-fade-in pointer-events-auto">
          <div className="bg-white rounded-[24px] p-6 w-full max-w-[320px] shadow-2xl animate-fade-up">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-[18px] font-bold text-ink">Change Password</h3>
              <button onClick={() => setShowPasswordModal(false)} className="text-ink-3 hover:text-ink">
                <X className="w-5 h-5" />
              </button>
            </div>
            {passwordStatus && (
              <div className={`mb-4 p-3 rounded-xl text-[12px] ${passwordStatus.type === 'error' ? 'bg-alert-bg text-alert border-alert/30' : 'bg-ok-bg text-ok border-ok/30'} border`}>
                {passwordStatus.msg}
              </div>
            )}
            <form onSubmit={handlePasswordSubmit} className="space-y-4">
              <div>
                <label className="block text-[12px] font-semibold text-ink-2 mb-1.5">Old Password</label>
                <input type="password" value={oldPassword} onChange={e => setOldPassword(e.target.value)} required className="w-full bg-slate-50 border border-slate-200 text-sm rounded-xl px-3 py-2 outline-none focus:border-brand-500" />
              </div>
              <div>
                <label className="block text-[12px] font-semibold text-ink-2 mb-1.5">New Password</label>
                <input type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} required minLength={6} className="w-full bg-slate-50 border border-slate-200 text-sm rounded-xl px-3 py-2 outline-none focus:border-brand-500" />
              </div>
              <button type="submit" className="w-full py-3 mt-2 rounded-xl font-bold text-[13px] text-white bg-brand-500 hover:bg-brand-600 transition-colors">
                Update Password
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Battalion Modal */}
      {showBattalionModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm px-6 animate-fade-in pointer-events-auto">
          <div className="bg-white rounded-[24px] p-6 w-full max-w-[320px] shadow-2xl animate-fade-up">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-[18px] font-bold text-ink">Change Battalion</h3>
              <button onClick={() => setShowBattalionModal(false)} className="text-ink-3 hover:text-ink">
                <X className="w-5 h-5" />
              </button>
            </div>
            {battalionStatus && (
              <div className={`mb-4 p-3 rounded-xl text-[12px] ${battalionStatus.type === 'error' ? 'bg-alert-bg text-alert border-alert/30' : 'bg-ok-bg text-ok border-ok/30'} border`}>
                {battalionStatus.msg}
              </div>
            )}
            <form onSubmit={handleBattalionSubmit} className="space-y-4">
              <div>
                <label className="block text-[12px] font-semibold text-ink-2 mb-1.5">Battalion</label>
                <select value={battalion} onChange={e => setBattalion(e.target.value)} className="w-full bg-slate-50 border border-slate-200 text-sm rounded-xl px-3 py-2 outline-none focus:border-brand-500">
                  <option value="7th Battalion">7th Battalion</option>
                  <option value="12th Battalion">12th Battalion</option>
                  <option value="Command HQ">Command HQ</option>
                </select>
              </div>
              <div>
                <label className="block text-[12px] font-semibold text-ink-2 mb-1.5">Location</label>
                <select value={location} onChange={e => setLocation(e.target.value)} className="w-full bg-slate-50 border border-slate-200 text-sm rounded-xl px-3 py-2 outline-none focus:border-brand-500">
                  <option value="Srinagar">Srinagar</option>
                  <option value="Jammu">Jammu</option>
                  <option value="Leh">Leh</option>
                </select>
              </div>
              <button type="submit" className="w-full py-3 mt-2 rounded-xl font-bold text-[13px] text-white bg-brand-500 hover:bg-brand-600 transition-colors">
                Update Assignment
              </button>
            </form>
          </div>
        </div>
      )}

      {showLogoutConfirm && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm px-6 animate-fade-in pointer-events-auto">
          <div className="bg-white rounded-[24px] p-6 w-full max-w-[320px] shadow-2xl animate-fade-up">
            <h3 className="text-[18px] font-bold text-ink mb-1.5">Sign Out</h3>
            <p className="text-[13px] text-ink-2 mb-6 leading-relaxed">Are you sure you want to log out of the ManoBal Portal?</p>
            <div className="flex items-center gap-3">
              <button 
                onClick={() => setShowLogoutConfirm(false)}
                className="flex-1 py-3 px-4 rounded-xl font-bold text-[13px] text-ink-3 bg-gray-100 hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button 
                onClick={() => {
                  setShowLogoutConfirm(false);
                  logout();
                }}
                className="flex-1 py-3 px-4 rounded-xl font-bold text-[13px] text-white bg-alert hover:bg-alert/90 shadow-[0_8px_16px_rgba(240,80,140,0.25)] transition-colors"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
