import { Pending } from "@/components/ui/state/Pending";

// Shown while the page waits for the backend's answer.
export default function Loading() {
  return <Pending label="Checking the backend…" />;
}
