export type AIChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type OTCDrugRecommendation = {
  title: string;
  rationale: string;
};

export type AIChatHandoff = {
  label: string;
  query: string;
};

export type AIChatResponse = {
  scopeStatus: "refused" | "otc_advice" | "doctor_referral" | "unavailable";
  message: string;
  warnings: string[];
  recommendedOTCDrugs: OTCDrugRecommendation[];
  handoffCTA: AIChatHandoff | null;
};
