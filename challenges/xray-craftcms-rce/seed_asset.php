<?php
/**
 * seed_asset.php — Creates a local filesystem volume + test asset in CraftCMS.
 * Run after `php craft install`. The resulting asset (id=1) is required for
 * the CVE-2025-32432 exploit's generate-transform endpoint to accept the request.
 */

chdir('/var/www/html');
require '/var/www/html/bootstrap.php';

// Bootstrap Craft CMS in console mode
/** @var craft\console\Application $app */
$app = require CRAFT_VENDOR_PATH . '/craftcms/cms/bootstrap/console.php';

// Don't actually run the Yii application loop — just use the services
$app->init();

try {
    // ── 1. Create upload directory ────────────────────────────────────────────
    $uploadsDir = CRAFT_BASE_PATH . '/web/uploads';
    if (!is_dir($uploadsDir)) {
        mkdir($uploadsDir, 0775, true);
    }

    // Write a minimal 1×1 PNG so the file actually exists on disk
    $png = base64_decode(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVQI12NgAAIABQAABjE+ibYAAAAASUVORK5CYII='
    );
    file_put_contents($uploadsDir . '/test.png', $png);

    // ── 2. Local filesystem ───────────────────────────────────────────────────
    $fs = new \craft\fs\Local([
        'name'    => 'CTF Local',
        'handle'  => 'ctfLocal',
        'hasUrls' => true,
        'url'     => '@web/uploads',
        'path'    => '@webroot/uploads',
    ]);

    if (!\Craft::$app->getFs()->saveFilesystem($fs)) {
        throw new \RuntimeException('Failed to save filesystem: ' . implode(', ', $fs->getFirstErrors()));
    }
    echo "[seed] Filesystem created id={$fs->id}\n";

    // ── 3. Volume ─────────────────────────────────────────────────────────────
    $volume = new \craft\models\Volume([
        'name'     => 'Images',
        'handle'   => 'images',
        'fsHandle' => 'ctfLocal',
        'subpath'  => '',
    ]);

    if (!\Craft::$app->getVolumes()->saveVolume($volume)) {
        throw new \RuntimeException('Failed to save volume: ' . implode(', ', $volume->getFirstErrors()));
    }
    echo "[seed] Volume created id={$volume->id}\n";

    // ── 4. Asset element ──────────────────────────────────────────────────────
    $rootFolder = \Craft::$app->getAssets()->getRootFolderByVolumeId($volume->id);
    if (!$rootFolder) {
        throw new \RuntimeException("Root folder not found for volume id={$volume->id}");
    }

    $asset = new \craft\elements\Asset();
    $asset->volumeId              = $volume->id;
    $asset->newFolderId           = $rootFolder->id;
    $asset->filename              = 'test.png';
    $asset->kind                  = 'image';
    $asset->size                  = strlen($png);
    $asset->tempFilePath          = $uploadsDir . '/test.png';
    $asset->avoidFilenameConflicts = true;
    $asset->newFilename           = 'test.png';

    if (!\Craft::$app->getElements()->saveElement($asset)) {
        throw new \RuntimeException('Failed to save asset: ' . implode(', ', $asset->getFirstErrors()));
    }
    echo "[seed] Asset created id={$asset->id} — use assetId={$asset->id} in exploit\n";
    echo "[seed] Done.\n";

} catch (\Throwable $e) {
    echo "[seed] Error: " . $e->getMessage() . "\n";
    // Non-fatal: app still starts, players can upload manually via /admin
    exit(1);
}
