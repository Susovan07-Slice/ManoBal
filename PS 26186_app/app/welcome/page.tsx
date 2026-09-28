import { StoryOnboarding } from "@/components/onboarding/StoryOnboarding";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Welcome to ManoBal",
  description: "Your daily wellness check-in.",
};

export default function WelcomePage() {
  return <StoryOnboarding />;
}
