<?php

$sourceApi = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json";
$file = "data.json";

$json = file_get_contents($sourceApi);
if ($json === false) exit("API ERROR");

$res = json_decode($json, true);
$list = $res['data']['list'] ?? [];

// load safely
$stored = [];
if (file_exists($file)) {
    $old = json_decode(file_get_contents($file), true);
    if (is_array($old)) {
        $stored = $old;
    }
}

// issue map
$map = [];
foreach ($stored as $row) {
    if (isset($row['issueNumber'])) {
        $map[$row['issueNumber']] = true;
    }
}

foreach ($list as $item) {
    if (!isset($item['issueNumber'], $item['number'])) continue;

    if (isset($map[$item['issueNumber']])) continue;

    $stored[] = [
        "issueNumber"=>$item['issueNumber'],
        "number"=>$item['number'],
        "time"=>time()
    ];

    $map[$item['issueNumber']] = true;
}

if (count($stored) > 10000) {
    $stored = array_slice($stored, -10000);
}

file_put_contents($file, json_encode($stored));
echo "OK";