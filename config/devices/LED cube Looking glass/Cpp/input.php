<?php

return [
	"start" => [
		[
			"name" => "cpp_code",
			"rules" => "required",
			"title" => "C++ code",
			"placeholder" => "",
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