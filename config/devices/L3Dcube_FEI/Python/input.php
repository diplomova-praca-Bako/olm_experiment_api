<?php

return [
	"start" => [
		[
			"name" => "python_code",
			"rules" => "required",
			"title" => "Python code",
			"placeholder" => "
setvoxel(1, 2, 3)
delay(1000)
clrvoxel(1, 2, 3)
delay(1000)
",
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