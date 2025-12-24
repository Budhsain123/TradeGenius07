<?php

$file = "data.json";
$perPage = 100;
$page = isset($_GET['page']) ? max(1, intval($_GET['page'])) : 1;

// file check
if (!file_exists($file)) {
    header("Content-Type: application/json");
    echo json_encode([
        "page"=>$page,
        "per_page"=>$perPage,
        "total_data"=>0,
        "data"=>[]
    ]);
    exit;
}

// decode safely
$content = file_get_contents($file);
$data = json_decode($content, true);

// json invalid / empty
if (!is_array($data)) {
    $data = [];
}

// latest first
$data = array_reverse($data);

$total = count($data);
$start = ($page - 1) * $perPage;
$pageData = array_slice($data, $start, $perPage);

header("Content-Type: application/json");
echo json_encode([
    "page"=>$page,
    "per_page"=>$perPage,
    "total_data"=>$total,
    "total_pages"=>ceil($total/$perPage),
    "data"=>$pageData
]);