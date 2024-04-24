<?php

namespace App\GraphQL\Queries;
use App\Models\Device;
use App\Models\Software;
use Illuminate\Database\Eloquent\Collection;

class SyncServer
{
    /**
     * @param  null  $_
     * @param  array<string, mixed>  $args
     */
    public function __invoke()
    {
        $finalSchema = [];
        $devices = Device::all();
        foreach($devices as $device) {
            $deviceType = $device->deviceType->name;
            $deviceOutput = config("devices.$deviceType.output");
            // dd($deviceOutput);
            $software = $device->software;
            
            $finalSchema[] = [
                'id' => $device->id,
                'name' => $device->name,
                'type' => $deviceType,
                'output' => $deviceOutput,
                'software' => $this->getSoftware($software, $deviceType)
            ];
        }

        return [
            'devices' => $finalSchema
        ];
    }



    private function getCommands(string $deviceType, string $softName): array  {
        $inputCommands = config("devices.$deviceType.$softName.input");

        $keys = array_keys($inputCommands);
        $commands = [];
        foreach($keys as $key) {
            $commands[] = [
                'name' => $key,
                'input' => $inputCommands[$key]
            ];
        }
        return $commands;
    }

    private function getSoftware(Collection $software, string $deviceType): array {
        $softSchema = [];
        foreach($software as $soft) {
            $softName = $soft->name;
            
            $softSchema[] = [
                'name' => $softName,
                'has_schema' => $softName != "openloop" && (strpos($deviceType, "L3Dcube") != false),
                'commands' => $this->getCommands($deviceType, $softName)
            ];
        }
        return $softSchema;
    }
}
