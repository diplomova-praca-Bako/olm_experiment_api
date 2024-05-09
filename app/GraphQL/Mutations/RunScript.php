<?php

namespace App\GraphQL\Mutations;

use App\Events\DataBroadcaster;
use App\Jobs\StartLEDProcess;
use App\Models\Device;
use App\Models\ExperimentLog;
use App\Jobs\StartReadingProcess;
use App\Helpers\Helpers;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Cache;


class RunScript
{
    /**
     * @param  null  $_
     * @param  array<string, mixed>  $args
     */
    public function __invoke($_, array $args)
    {
        $fileName = storage_path("outputs/". uniqid() .".txt");
        file_put_contents($fileName, "");
        set_time_limit(200);
        $date = filemtime($fileName);

        $device = Device::find($args['runScriptInput']['device']['deviceID']);
        $deviceName = $args['runScriptInput']['device']['deviceName'];
        $software = $args['runScriptInput']['device']['software'];
        $scriptName = $args['runScriptInput']['scriptName'];
        $scriptFileName = Helpers::getScriptName($scriptName, base_path()."/server_scripts/$deviceName/$software");

        if ($scriptFileName == null) {
            broadcast(new DataBroadcaster(null, $device->name, "No such script or file in directory", false));
            return;
        }

        $path = base_path()."/server_scripts/$deviceName/$software/".$scriptFileName;
        if ($scriptName == "startLocal") {
            $schemaFileName = explode(".", Helpers::getSchemaNameForLocalStart($software));
        } else {
            $schemaFileName = explode(".", $args['runScriptInput']['fileName']);
        }

        $demoFileName = explode(".", $args['runScriptInput']['demoName']);
        
        if (strpos($deviceName, "LED") !== false) {
            $args['runScriptInput']['inputParameter'] = $args['runScriptInput']['inputParameter'] . ",uploaded_file:". storage_path('tmp/uploads/') . ",demo_name:". $demoFileName[0];
        } else {
            $args['runScriptInput']['inputParameter'] = $args['runScriptInput']['inputParameter'] . ",uploaded_file:". storage_path('tmp/uploads/') . ",file_name:". $schemaFileName[0];
        }

        Log::channel('server')->error("ERRORMESSAGE: " . $args['runScriptInput']['inputParameter']);
        $experiment = ExperimentLog::create([
            'device_id' => $device->id,
            'input_arguments' => $args['runScriptInput']['inputParameter'],
            'output_path' => $fileName,
            'software_name' => $software,
            'schema_name' => $schemaFileName[0],
            'process_pid' => -1,
            'started_at' => date("Y-m-d H:i:s")
        ]);

        
        $uniqueId = uniqid();
        $errorResult = null;

        if (strpos($deviceName, "LED") !== false) {
            $LEDProcess = new StartLEDProcess($date, $fileName, $path, $device, $args, $experiment, $deviceName, $software, $uniqueId);
            dispatch($LEDProcess)->onQueue("Reading");
            
            sleep(4); //wait for experiment to finish compiling code or generating instructions to see possible errors

            $errorResult = Cache::get('job-result-' . $uniqueId);
            Log::debug('ErrorResult', [$errorResult]);
        } else {
            $readingProcess = new StartReadingProcess($date, $fileName, $path, $device, $args, $experiment, $deviceName);
            dispatch($readingProcess)->onQueue("Reading");
        }

        if ($errorResult && $errorResult['status'] === 'error') {
            return[
                'status' => 'error',
                'experimentID' => $errorResult['experimentID'],
                'errorMessage' => $errorResult['errorMessage']
            ];
        } else{
            return [
                'status' => 'success',
                'experimentID' => $experiment->id,
                'errorMessage' => ''
            ];
        }
    }
}
