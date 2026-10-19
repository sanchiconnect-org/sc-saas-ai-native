#!/usr/bin/env node
/*
 * SAN-1580: one-way mirror of selected workspace docs to Linear documents.
 *
 * Reads docs/linear-mirror.json, and for each listed file creates or updates
 * a Linear document (same title, in one project) whose body is a provenance
 * header (source path, commit SHA, sync time, content hash, "the repository
 * wins any conflict") followed by the file. After every write it reads the
 * document back and checks the header and length survived; any failure is
 * reported as a GitHub error annotation and the run exits 1.
 *
 * Env: LINEAR_API_KEY (required unless --dry-run), LINEAR_DOCS_PROJECT_ID
 * (overrides the config's projectId), LINEAR_API_URL (tests only),
 * GITHUB_SHA (falls back to `git rev-parse HEAD`).
 * Flags: --dry-run (no network; prints what would be written),
 *        --config <path> (default docs/linear-mirror.json).
 */
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { execSync } from 'node:child_process';

const args = process.argv.slice(2);
const DRY_RUN = args.includes('--dry-run');
const configIdx = args.indexOf('--config');
const CONFIG_PATH = configIdx >= 0 ? args[configIdx + 1] : 'docs/linear-mirror.json';
const API_URL = process.env.LINEAR_API_URL || 'https://api.linear.app/graphql';
const API_KEY = process.env.LINEAR_API_KEY || '';
/* Readback must keep at least this share of the written length (Linear normalises markdown slightly). */
const MIN_READBACK_RATIO = 0.9;

function fail(message) {
  console.log(`::error title=Linear doc mirror::${message}`);
  console.error(`ERROR: ${message}`);
}

function commitSha() {
  if (process.env.GITHUB_SHA) return process.env.GITHUB_SHA;
  try {
    return execSync('git rev-parse HEAD', { encoding: 'utf8' }).trim();
  } catch {
    return 'unknown';
  }
}

export function buildBody({ path, source, sha, syncedAt }) {
  const hash = createHash('sha256').update(source).digest('hex');
  const header = [
    `> **Repository mirror. Do not edit here.** The repository wins any conflict: change \`${path}\` in the workspace repo and merge to \`main\`; this document is overwritten on the next sync.`,
    `>`,
    `> Source: \`${path}\` · Commit: \`${sha}\` · Synced: ${syncedAt} · Content SHA-256: \`${hash}\``,
    '',
    '---',
    '',
  ].join('\n');
  return { hash, body: header + source };
}

async function gql(query, variables) {
  const res = await fetch(API_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: API_KEY },
    body: JSON.stringify({ query, variables }),
  });
  const text = await res.text();
  let json;
  try {
    json = JSON.parse(text);
  } catch {
    throw new Error(`Linear API HTTP ${res.status}: ${text.slice(0, 300)}`);
  }
  if (!res.ok || json.errors) {
    throw new Error(`Linear API HTTP ${res.status}: ${JSON.stringify(json.errors || json).slice(0, 500)}`);
  }
  return json.data;
}

async function projectDocuments(projectId) {
  const docs = [];
  let after = null;
  for (;;) {
    const data = await gql(
      `query($id: String!, $after: String) {
        project(id: $id) { documents(first: 100, after: $after) {
          nodes { id title content } pageInfo { hasNextPage endCursor } } }
      }`,
      { id: projectId, after },
    );
    if (!data.project) throw new Error(`Linear project ${projectId} not found`);
    docs.push(...data.project.documents.nodes);
    if (!data.project.documents.pageInfo.hasNextPage) return docs;
    after = data.project.documents.pageInfo.endCursor;
  }
}

async function mirrorOne(entry, ctx) {
  const source = readFileSync(entry.path, 'utf8');
  const { hash, body } = buildBody({ path: entry.path, source, sha: ctx.sha, syncedAt: ctx.syncedAt });

  if (DRY_RUN) {
    console.log(`[dry-run] ${entry.path} -> "${entry.title}" (${body.length} chars, sha256 ${hash.slice(0, 12)})`);
    return;
  }

  const matches = ctx.existing.filter((d) => d.title === entry.title);
  if (matches.length > 1) throw new Error(`${matches.length} Linear documents are titled "${entry.title}"; remove the extras`);
  const current = matches[0];

  if (current && current.content.includes(`Content SHA-256: \`${hash}\``)) {
    console.log(`unchanged ${entry.path} (Linear document ${current.id})`);
    return;
  }

  let id;
  if (current) {
    const data = await gql(
      `mutation($id: String!, $input: DocumentUpdateInput!) {
        documentUpdate(id: $id, input: $input) { success document { id } } }`,
      { id: current.id, input: { content: body } },
    );
    if (!data.documentUpdate.success) throw new Error(`documentUpdate failed for ${entry.path}`);
    id = data.documentUpdate.document.id;
  } else {
    const data = await gql(
      `mutation($input: DocumentCreateInput!) {
        documentCreate(input: $input) { success document { id } } }`,
      { input: { title: entry.title, content: body, projectId: ctx.projectId } },
    );
    if (!data.documentCreate.success) throw new Error(`documentCreate failed for ${entry.path}`);
    id = data.documentCreate.document.id;
  }

  /* Read the document back and check the write really landed. */
  const back = await gql(`query($id: String!) { document(id: $id) { id content url } }`, { id });
  const content = back.document && back.document.content ? back.document.content : '';
  const problems = [];
  if (!content.includes(`Content SHA-256: \`${hash}\``)) problems.push('content hash missing from readback');
  if (!content.includes(`Commit: \`${ctx.sha}\``)) problems.push('commit SHA missing from readback');
  if (content.length < body.length * MIN_READBACK_RATIO) problems.push(`readback is ${content.length} chars, wrote ${body.length}`);
  if (problems.length > 0) throw new Error(`${entry.path}: written but readback failed (${problems.join('; ')})`);

  console.log(`${current ? 'updated' : 'created'} ${entry.path} -> ${back.document.url || id}`);
}

async function main() {
  const config = JSON.parse(readFileSync(CONFIG_PATH, 'utf8'));
  const projectId = process.env.LINEAR_DOCS_PROJECT_ID || config.projectId;
  if (!Array.isArray(config.docs) || config.docs.length === 0) {
    fail(`${CONFIG_PATH} lists no docs`);
    return 1;
  }
  if (!DRY_RUN && !API_KEY) {
    fail('LINEAR_API_KEY is not set (add it as a repository secret)');
    return 1;
  }
  if (!DRY_RUN && !projectId) {
    fail(`no Linear project: set projectId in ${CONFIG_PATH} or the LINEAR_DOCS_PROJECT_ID variable`);
    return 1;
  }

  const ctx = { sha: commitSha(), syncedAt: new Date().toISOString(), projectId, existing: [] };
  if (!DRY_RUN) ctx.existing = await projectDocuments(projectId);

  let failures = 0;
  for (const entry of config.docs) {
    try {
      await mirrorOne(entry, ctx);
    } catch (err) {
      failures++;
      fail(err.message);
    }
  }
  if (failures > 0) {
    fail(`${failures} of ${config.docs.length} docs failed to mirror`);
    return 1;
  }
  console.log(`mirrored ${config.docs.length} docs at ${ctx.sha}`);
  return 0;
}

/* exitCode, not process.exit(): exiting while fetch sockets close can abort Node on Windows. */
main().then(
  (code) => {
    process.exitCode = code;
  },
  (err) => {
    fail(err.message);
    process.exitCode = 1;
  },
);
