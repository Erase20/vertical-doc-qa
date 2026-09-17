"use client";

import { ShieldAlert } from "lucide-react";

interface Props {
  level: "crisis" | "normal";
}

export function SafetyNotice({ level }: Props) {
  if (level !== "crisis") {
    return null;
  }

  return (
    <div className="safety-notice" role="alert">
      <ShieldAlert size={17} />
      <div>
        <strong>当前问题已进入安全支持流程</strong>
        <p>如果存在立即危险，请联系当地紧急服务或身边可信任的人。</p>
      </div>
    </div>
  );
}
