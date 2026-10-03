// Run inside the frontend container by `make smoke-stack` (node reads it
// from stdin): the production page must say the backend is up and carry
// the security policy.
const response = await fetch("http://localhost:3000/");
const page = await response.text();
const problems = [];
if (!response.ok) problems.push(`HTTP ${response.status}`);
if (!page.includes("Backend: up")) problems.push("the backend is not up");
if (!response.headers.get("content-security-policy")) {
  problems.push("no Content-Security-Policy header");
}
if (problems.length > 0) {
  console.error(`smoke: ${problems.join("; ")}\n${page.slice(0, 500)}`);
  process.exit(1);
}
console.log("smoke: the frontend serves the page and the backend is up");
