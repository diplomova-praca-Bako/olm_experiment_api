<?php

namespace App\GraphQL\Mutations;

use App\Events\DataBroadcaster;
use App\Models\Device;
use App\Models\ExperimentLog;
use App\Jobs\StartReadingProcess;
use App\Helpers\Helpers;
use Illuminate\Support\Facades\Log;
use Symfony\Component\Process\Process;


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
        
        if (strpos($deviceName, "L3Dcube") !== false) {
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

        
        $status='success';
        $errorMessage='';

        if (strpos($deviceName, "L3Dcube") !== false) {  // if we are processing L3Dcube experiment, dont start reading
            $process = new Process([
                "$path",
                '--port', $device->port,
                '--output', $fileName,
                '--input', $args['runScriptInput']['inputParameter']
            ]);

            $process->start();
            sleep(2);
            if ($process->getPid() != null) {
                $experiment->update([
                    'process_pid' => $process->getPid()
                ]);
            }
            while($process->isRunning()) {
                clearstatcache();
            };
            // clearstatcache();

            $errorOutput = $process->getErrorOutput();
            Log::debug('ErrorOutputLog', [$errorOutput]);
            
            if ($errorOutput !== "") {
                $status = 'error';
                // cleaning errors
                if ($software === "C") { // C language errors
                    Log::debug("SoftwareCerror", []);
            
                    // Specifically extract the error message without file paths and line/column numbers
                    //this is for compilation errors
                    preg_match("/error: '.*?' was not declared in this scope/", $errorOutput, $matches);
                                                    //if no compilation error, clean serial comm errors
                    $errorMessage = $matches[0] ?? ltrim(preg_replace('/\s*\/[^:]+:\d+:\d+:\s*/', '; ', $errorOutput), "; ");
                } else { // Python language errors
                    Log::debug("SoftwarePythonerror", []);
                    preg_match('/\n(.+Error:.+)$/', $errorOutput, $matches);
                    $errorMessage = $matches[1] ?? 'Error not found';
                }
            }
            
            Log::debug('error message log', [$errorMessage]);

            Log::channel('server')->error("ERRORMESSAGE: " . $process->getErrorOutput());
            Log::channel('server')->info("PROCESS OUTPUT: " . $process->getOutput());
            
        } else {
            $readingProcess = new StartReadingProcess($date, $fileName, $path, $device, $args, $experiment, $deviceName);
            dispatch($readingProcess)->onQueue("Reading");
        }

        return [
            'status' => $status,
            'experimentID' => $experiment->id,
            'errorMessage' => $errorMessage
        ];
    }
}
