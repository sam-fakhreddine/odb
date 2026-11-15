// Catches: version-policy, release-safety, and version propagation regressions.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = process.env.RELEASE_PLEASE_ROOT;
assert.ok(root, "Set RELEASE_PLEASE_ROOT to the release-please package directory");
assert.equal(require(path.join(root, "package.json")).version, "17.3.0");
const { Version } = require(path.join(root, "build/src/version"));
const { DefaultVersioningStrategy } = require(path.join(root, "build/src/versioning-strategies/default"));
const { parseConventionalCommits } = require(path.join(root, "build/src/commit"));
const { DefaultChangelogNotes } = require(path.join(root, "build/src/changelog-notes/default"));
const { PyProjectToml } = require(path.join(root, "build/src/updaters/python/pyproject-toml"));
const { Generic } = require(path.join(root, "build/src/updaters/generic"));
const { Changelog } = require(path.join(root, "build/src/updaters/changelog"));
const { Manifest } = require(path.join(root, "build/src/manifest"));
const yaml = require(require.resolve("js-yaml", { paths: [root] }));
const read = file => fs.readFileSync(file, "utf8");
const config = JSON.parse(read("release-please-config.json"));
const manifest = JSON.parse(read(".release-please-manifest.json"));
const workflow = yaml.load(read(".github/workflows/auto-semver.yml"));
const strategy = new DefaultVersioningStrategy({
  bumpMinorPreMajor: config["bump-minor-pre-major"],
  bumpPatchForMinorPreMajor: config["bump-patch-for-minor-pre-major"],
});

async function main() {
  for (const [current, message, expected] of [
    ["0.1.0", "fix: repair routing", "0.1.1"],
    ["0.1.0", "feat: add routing", "0.2.0"],
    ["0.1.0", "chore!: replace routing", "0.2.0"],
    ["1.2.3", "fix: repair routing", "1.2.4"],
    ["1.2.3", "feat: add routing", "1.3.0"],
    ["1.2.3", "fix!: replace routing", "2.0.0"],
  ]) {
    const commits = parseConventionalCommits([{ sha: "abc123", message, files: [] }]);
    assert.equal(strategy.bump(Version.parse(current), commits).toString(), expected, message);
  }
  const notes = new DefaultChangelogNotes();
  const options = {
    owner: "example", repository: "odb", version: "0.2.0",
    changelogSections: config["changelog-sections"],
  };
  const breaking = parseConventionalCommits([{ sha: "abc123", message: "chore!: replace routing", files: [] }]);
  const entry = await notes.buildNotes(breaking, options);
  assert.match(entry, /BREAKING CHANGES/);
  assert.match(entry, /replace routing/);
  const documentation = parseConventionalCommits([{ sha: "abc123", message: "docs: improve guide", files: [] }]);
  const docsEntry = await notes.buildNotes(documentation, options);
  assert.ok(docsEntry.split("\n").length <= 1, "documentation alone should not create a release proposal");

  const version = Version.parse("0.2.0");
  assert.match(new PyProjectToml({ version }).updateContent(read("pyproject.toml")), /version = "0\.2\.0"/);
  const readme = new Generic({ version }).updateContent(read("README.md"));
  assert.match(readme, /\*\*v0\.2\.0 - early development/);
  assert.match(readme, /git clone --branch v0\.2\.0/);
  assert.equal((readme.match(/x-release-please-version/g) || []).length, 2);
  const changelog = new Changelog({ version, changelogEntry: entry }).updateContent(read("CHANGELOG.md"));
  assert.ok(changelog.includes("replace routing") && changelog.includes("0.1.0"));

  assert.equal(manifest["."], read("pyproject.toml").match(/^version = "([^"]+)"$/m)[1]);
  assert.equal(config["bootstrap-sha"], "0208b1992e7ef9f3518f156c0dde8431b2840a57");
  assert.equal(config["release-type"], "python");
  assert.equal(config["skip-github-release"], true);
  assert.deepEqual(config.packages["."]["extra-files"], ["README.md"]);
  assert.deepEqual(workflow.on.push.branches, ["main"]);
  assert.ok(Object.hasOwn(workflow.on, "workflow_dispatch"));
  assert.equal(workflow.permissions.contents, "read");
  const job = workflow.jobs.propose;
  assert.match(job.if, /github\.ref == 'refs\/heads\/main'/);
  assert.match(job.if, /github\.event_name == 'workflow_dispatch'/);
  assert.match(job.if, /vars\.ODB_AUTO_SEMVER == 'true'/);
  assert.match(job.steps[0].run, /exit 1/);
  assert.equal(job.steps[0].env.RELEASE_TOKEN, "${{ secrets.RELEASE_PLEASE_TOKEN }}");
  const action = job.steps[1];
  assert.equal(action.uses, "googleapis/release-please-action@5c625bfb5d1ff62eadeeb3772007f7f66fdcf071");
  assert.equal(action.with["skip-github-release"], true);
  assert.equal(action.with.token, "${{ secrets.RELEASE_PLEASE_TOKEN }}");
  assert.equal(action.with["config-file"], "release-please-config.json");
  assert.equal(action.with["manifest-file"], ".release-please-manifest.json");
  const autoMerge = yaml.load(read(".github/workflows/auto-merge.yml"));
  assert.deepEqual(autoMerge.on.pull_request_target.branches, ["main"]);
  assert.deepEqual(autoMerge.on.pull_request_target.types, ["opened", "reopened", "synchronize", "ready_for_review"]);
  const mergeJob = autoMerge.jobs.enable;
  assert.match(mergeJob.if, /!github\.event\.pull_request\.draft/);
  assert.match(mergeJob.if, /\["OWNER","MEMBER","COLLABORATOR"\]/);
  assert.match(mergeJob.steps[0].run, /--auto --merge --match-head-commit "\$HEAD_SHA"/);
  assert.match(mergeJob.steps[0].run, /exit 1/);
  assert.equal(mergeJob.steps[0].env.GH_TOKEN, "${{ secrets.RELEASE_PLEASE_TOKEN }}");
  assert.equal(mergeJob.steps[0].env.HEAD_SHA, "${{ github.event.pull_request.head.sha }}");
  assert.ok(!mergeJob.steps.some(step => step.uses), "pull_request_target must not check out PR code");
  let pending = true;
  const fake = {
    buildPullRequests: async () => [{ version: "0.3.0" }],
    async *findMergedReleasePullRequests() { if (pending) yield {}; },
    findOpenReleasePullRequests: async () => [],
    findSnoozedReleasePullRequests: async () => [],
    createOrUpdatePullRequest: async () => 42,
    sequentialCalls: true,
    logger: { warn() {} },
  };
  assert.deepEqual(await Manifest.prototype.createPullRequests.call(fake), []);
  pending = false;
  assert.deepEqual(await Manifest.prototype.createPullRequests.call(fake), [42]);
  console.log("PASS release-please policy, updaters, changelog and workflow safeguards");
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
