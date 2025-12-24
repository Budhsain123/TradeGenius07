<?php

$sourceApi = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json";
$file = "data.json";

$response = json_decode(file_get_contents($sourceApi), true);
$list = $response['data']['list'] ?? [];

// existing data
$stored = file_exists($file)
    ? json_decode(file_get_contents($file), true)
    : [];

// existing issueNumber map
$exists = [];
foreach ($stored as $row) {
    $exists[$row['issueNumber']] = true;
}

// save only new issueNumber
foreach ($list as $item) {
    $issue = $item['issueNumber'];

    if (isset($exists[$issue])) {
        continue; // duplicate skip
    }

    $stored[] = [
        "issueNumber" => $issue,
        "number" => $item['number'],
        "time" => time()
    ];

    $exists[$issue] = true;
}

// max 10,000 records
if (count($stored) > 10000) {
    $stored = array_slice($stored, -10000);
}

// save file
file_put_contents($file, json_encode($stored));

echo "OK";