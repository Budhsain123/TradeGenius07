<?php

$file = "data.json";
$perPage = 100;

$page = isset($_GET['page']) ? max(1, intval($_GET['page'])) : 1;

if (!file_exists($file)) {
    echo json_encode(["data" => [], "total" => 0]);
    exit;
}

$data = json_decode(file_get_contents($file), true);

// latest first
$data = array_reverse($data);

$total = count($data);
$totalPages = ceil($total / $perPage);

$start = ($page - 1) * $perPage;
$pageData = array_slice($data, $start, $perPage);

header("Content-Type: application/json");
echo json_encode([
    "page" => $page,
    "per_page" => $perPage,
    "total_data" => $total,
    "total_pages" => $totalPages,
    "data" => $pageData
]);