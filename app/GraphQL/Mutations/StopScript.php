<?php

namespace App\GraphQL\Mutations;
use App\Models\Device;
use App\Models\ExperimentLog;
use Symfony\Component\Process\Process;
use Illuminate\Support\Facades\Log;


class StopScript
{
    /**
     * @param  null  $_
     * @param  array<string, mixed>  $args
     */
    public function __invoke($_, array $args)
    {
        set_time_limit(100);
        $device = Device::find($args['runScriptInput']['device']['deviceID']);
        $deviceName = $args['runScriptInput']['device']['deviceName'];

        $experimentID = $args['runScriptInput']['experimentID'];

        $experiment = ExperimentLog::find($experimentID);

        if (!posix_getpgid($experiment->process_pid)) {
            return [
                'status' => 'error',
                'experimentID' => $experimentID,
                'errorMessage' => "Experiment is finished!"
            ];
        }

        $schema_name = explode(".",$experiment->schema_name)[0];
        $demo_name = explode(".",$experiment->demo_name)[0];


        $process = new Process([
            "./../server_scripts/$deviceName/stop.py",
            '--port', $device->port,
            '--software', $experiment->software_name,
            '--fileName', $schema_name,
            '--demoName', $demo_name
        ]);

        $process->start();
        sleep(1);
        broadcast(null);

        $pid = $experiment->process_pid;
        $allProcesses = $this->getAllChildProcesses($pid);
        $allPids = array_merge([$pid], $allProcesses);

        $experiment->update([
            'stopped_at' => date("Y-m-d H:i:s")
        ]);

        foreach ($allPids as $killpid) {
            $killProcess = new Process([
                "kill","-9","$killpid"
            ]);
            
            $killProcess->start();
            sleep(1);

            if ($killProcess->getErrorOutput())
                return [
                    'status' => 'error',
                    'experimentID' => $experimentID,
                    'errorMessage' => $killProcess->getErrorOutput()
                ];
        }

        return [
            'status' => 'success',
            'experimentID' => $experimentID,
            'errorMessage' => ''
        ];
    }


    protected function getAllChildProcesses($pid)
    {
        $process = new Process(["pstree -p ". $pid ." | grep -o '([0-9]\+)' | grep -o '[0-9]\+'"]);

        $process->run();
        $allProcesses = array_filter(explode("\n", $process->getOutput()));

        return $allProcesses;
    }
}
