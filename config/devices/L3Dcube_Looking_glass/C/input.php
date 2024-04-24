<?php

return [
	"start" => [
		[
			"name" => "c_code",
			"rules" => "required",
			"title" => "C code",
			"placeholder" => "
setPixelColor({1,1,1}, {255, 0, 0});
sleep(500);",
			"type" => "textarea",
			"row" => 1,
			"order" => 1,
			"rows" => 12,
			"multiline" => true
		],
	
		[
			"name" => "uploaded_code_file",
			"rules" => "required",
			"title" => "Input File",
			"type" => "file",
			"row" => 2,
			"order" => 2,
			"meaning" => "parent_schema"
		],
		
	],
	"stop" => [],
	"change" => []
];