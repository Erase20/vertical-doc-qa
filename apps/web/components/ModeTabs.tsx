"use client";

import { BookOpenCheck, GraduationCap, LibraryBig } from "lucide-react";

import type { DomainMode } from "@/lib/types";

const MODES = [
  { id: "psychoeducation", label: "心理科普", icon: GraduationCap },
  { id: "assessment", label: "测评说明", icon: BookOpenCheck },
  { id: "professional", label: "专业资料", icon: LibraryBig }
] satisfies Array<{ id: DomainMode; label: string; icon: typeof GraduationCap }>;

interface Props {
  mode: DomainMode;
  onChange: (mode: DomainMode) => void;
}

export function ModeTabs({ mode, onChange }: Props) {
  return (
    <div className="mode-tabs" role="tablist" aria-label="问答模式">
      {MODES.map((item) => {
        const Icon = item.icon;
        return (
          <button
            className={item.id === mode ? "mode-tab active" : "mode-tab"}
            key={item.id}
            type="button"
            role="tab"
            aria-selected={item.id === mode}
            onClick={() => onChange(item.id)}
          >
            <Icon size={14} />
            {item.label}
          </button>
        );
      })}
    </div>
  );
}
