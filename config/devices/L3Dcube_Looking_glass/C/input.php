<?php

return [
	"start" => [
		[
			"name" => "c_code",
			"rules" => "required",
			"title" => "C code",
			"placeholder" => "
while (true) {
	setLed({0,0,0}, {255, 0, 0});
	setLed({0,0,1}, {255, 0, 0});
	setLed({0,0,2}, {255, 0, 0});
	setLed({0,0,3}, {255, 0, 0});
	setLed({0,0,4}, {255, 0, 0});
	setLed({0,0,5}, {255, 0, 0});
	setLed({0,0,6}, {255, 0, 0});
	setLed({0,0,7}, {255, 0, 0});
	sleep(500);
	clearLed({0,0,0});
	clearLed({0,0,1});
	clearLed({0,0,2});
	clearLed({0,0,3});
	clearLed({0,0,4});
	clearLed({0,0,5});
	clearLed({0,0,6});
	clearLed({0,0,7});
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