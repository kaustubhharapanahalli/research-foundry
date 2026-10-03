import { connection } from "next/server";

import { BackendStatus } from "@/features/status/components/BackendStatus";
import { fetchHealth } from "@/lib/server/backend";

export default async function HomePage() {
  // Rendered per request: the backend's state is read at request time.
  await connection();
  const health = await fetchHealth();
  return (
    <>
      <h1>{{ cookiecutter.project_name }}</h1>
      <BackendStatus health={health} />
    </>
  );
}
