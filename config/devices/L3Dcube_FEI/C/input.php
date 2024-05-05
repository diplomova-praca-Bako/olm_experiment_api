<?php

return [
	"start" => [
		[
			"name" => "c_code",
			"rules" => "required",
			"title" => "C code",
			"placeholder" => "
for (int x = 0; x < 8; x++) {
	for (int y = 0; y < 8; y++) {
		for (int z = 0; z < 8; z++) {
			setLed(x,y,z);
			sleep(30);
		}
	}
}",
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
