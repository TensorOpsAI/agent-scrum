// Automated demo recorder for the El País branch.
// Drives the whole feature set headlessly and records a video via Playwright.
//
// Prereqs: backend on :8000 and frontend on :5173 already running (make dev).
// Usage:   node scripts/record-demo.mjs
import { chromium } from 'playwright';

const FRONTEND_URL = 'http://localhost:5173';
const BACKEND_URL = 'http://localhost:8000';
const OUT_DIR = new URL('../demo-recordings/', import.meta.url).pathname;

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function waitForServer(url, label, attempts = 20) {
  for (let i = 0; i < attempts; i++) {
    try {
      const res = await fetch(url);
      if (res.ok || res.status < 500) return;
    } catch {
      // not up yet
    }
    await sleep(500);
  }
  throw new Error(`${label} not reachable at ${url} — make sure "make dev" is running.`);
}

async function resetBackend() {
  const res = await fetch(`${BACKEND_URL}/api/settings/reset`, { method: 'POST' });
  if (!res.ok) throw new Error(`Reset failed: HTTP ${res.status}`);
  console.log('[demo] backend reset — fresh Redacción board seeded');
}

async function main() {
  await waitForServer(`${BACKEND_URL}/docs`, 'backend');
  await waitForServer(FRONTEND_URL, 'frontend');
  await resetBackend();

  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    recordVideo: { dir: OUT_DIR, size: { width: 1440, height: 900 } },
  });

  // Suppress the auto-triggered replay so we control exactly when it fires.
  await context.addInitScript(() => {
    window.localStorage.setItem('agent-scrum:demo-replay-played', 'true');
  });

  const page = await context.newPage();
  console.log('[demo] navigating to app…');
  await page.goto(FRONTEND_URL);
  await page.waitForTimeout(1200);

  // --- Onboarding walkthrough ---
  const welcomeHeading = page.getByText('Bienvenido a la redacción con IA');
  if (await welcomeHeading.isVisible({ timeout: 5000 }).catch(() => false)) {
    console.log('[demo] walking through onboarding…');
    for (let i = 0; i < 3; i++) {
      await page.waitForTimeout(1500);
      await page.getByRole('button', { name: 'Siguiente' }).click();
    }
    await page.waitForTimeout(1500);
    await page.getByRole('button', { name: 'Empezar' }).click();
  }
  await page.waitForTimeout(1200);

  // --- Scripted 30s swarm replay (board is still empty at this point) ---
  console.log('[demo] triggering the 30s scripted swarm replay…');
  const replayButton = page.getByRole('button', { name: /Repetir demo de 30 segundos|Generar Artículos/ }).first();
  await replayButton.waitFor({ state: 'visible', timeout: 10000 });
  // Prefer the actual replay button if present, else fall back to Generar Artículos.
  const hasReplay = await page.getByRole('button', { name: 'Repetir demo de 30 segundos' }).isVisible().catch(() => false);
  if (hasReplay) {
    await page.getByRole('button', { name: 'Repetir demo de 30 segundos' }).click();
  } else {
    await page.getByRole('button', { name: 'Generar Artículos' }).first().click();
  }
  await page.waitForTimeout(28000);

  // --- Vista previa on the now-published article ---
  console.log('[demo] opening Vista previa…');
  const previewButton = page.getByRole('button', { name: 'Vista previa' }).first();
  if (await previewButton.isVisible({ timeout: 5000 }).catch(() => false)) {
    await previewButton.click();
    await page.waitForTimeout(4000);
    await page.mouse.click(10, 10); // click backdrop to close
    await page.waitForTimeout(800);
  } else {
    console.log('[demo] no published card yet — skipping Vista previa');
  }

  // --- Story detail with Spanish activity log (the published GPT-6 story has a full comment trail) ---
  console.log('[demo] opening a story detail panel…');
  const richCard = page.locator('[role="button"]').filter({ hasText: 'OpenAI' }).first();
  const anyCard = (await richCard.isVisible().catch(() => false))
    ? richCard
    : page.locator('[role="button"]').filter({ hasText: /./ }).first();
  await anyCard.click().catch(() => {});
  await page.waitForTimeout(3500);
  await page.mouse.click(10, 10);
  await page.waitForTimeout(800);

  // --- Tendencias: add real trending items ---
  console.log('[demo] opening Tendencias and adding real news items…');
  await page.getByRole('button', { name: 'Tendencias' }).click();
  await page.waitForTimeout(800);
  const addButtons = page.getByRole('button', { name: 'Añadir al tablero' });
  await addButtons.nth(0).click(); // Balogun / FIFA (sports)
  await page.waitForTimeout(1800);
  const addButtonsAfter = page.getByRole('button', { name: 'Añadir al tablero' });
  const remaining = await addButtonsAfter.count();
  if (remaining > 0) {
    await addButtonsAfter.nth(remaining - 1).click(); // Nakamura (science)
    await page.waitForTimeout(1800);
  }
  await page.mouse.click(10, 10);
  await page.waitForTimeout(1000);

  // --- Start the real swarm on the newly added trending articles ---
  console.log('[demo] starting live automation…');
  const startSwarm = page.getByRole('button', { name: 'Iniciar automatización' });
  if (await startSwarm.isVisible({ timeout: 3000 }).catch(() => false)) {
    await startSwarm.click();
    await page.waitForTimeout(20000);
  }

  // --- Settings + Agent manager, Spanish copy ---
  console.log('[demo] showing settings and agent manager…');
  await page.getByRole('button', { name: 'Configuración', exact: true }).click();
  await page.waitForTimeout(2500);
  await page.mouse.click(10, 10);
  await page.waitForTimeout(600);

  const manageAgents = page.getByRole('button', { name: 'Gestionar agentes' });
  if (await manageAgents.isVisible({ timeout: 3000 }).catch(() => false)) {
    await manageAgents.click();
    await page.waitForTimeout(3500);
    await page.mouse.click(10, 10);
  }

  await page.waitForTimeout(1000);
  await context.close();
  await browser.close();
  console.log(`[demo] done — video saved under ${OUT_DIR}`);
}

main().catch((err) => {
  console.error('[demo] failed:', err);
  process.exit(1);
});
