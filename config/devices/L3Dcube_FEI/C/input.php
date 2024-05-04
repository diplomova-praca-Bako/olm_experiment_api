<?php

return [
	"start" => [
		[
			"name" => "c_code",
			"rules" => "required",
			"title" => "C code",
			"placeholder" => "
for (int x = 0; x < cube_size; x++) {
	for (int y = 0; y < cube_size; y++) {
		for (int z = 0; z < cube_size; z++) {
			setvoxel(x,y,z);
			delay(30);
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
