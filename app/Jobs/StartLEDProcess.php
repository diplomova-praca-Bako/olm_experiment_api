<?php

namespace App\Jobs;

use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use Symfony\Component\Process\Process;
use App\Models\ExperimentLog;
use App\Models\Device;
use Illuminate\Support\Facades\Log;
use App\Events\DataBroadcaster;
use App\Helpers\Helpers;
use Illuminate\Support\Facades\Cache;
use Throwable;

class StartLEDProcess implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    protected $uniqueId;
    protected $experiment;
    protected $date;
    protected $fileName;
    protected $path;
    protected $device;
    protected $args;
    protected $deviceType;
    protected $software;

    public function __construct(int $date, string $fileName, string $path, Device $device, $args, ExperimentLog $experiment, string $deviceType, string $software, string $uniqueId)
    {
        $this->uniqueId = $uniqueId;
        $this->date = $date;
        $this->fileName = $fileName;
        $this->path = $path;
        $this->device = $device;
        $this->args = $args;
        $this->experiment = $experiment;
        $this->deviceType = $deviceType;
        $this->software = $software;
    }

    public function handle()
    {
        try {
            $process = new Process([
                "$this->path",
                '--port', $this->device->port,
                '--output', $this->fileName,
                '--input', $this->args['runScriptInput']['inputParameter']
            ]);

            $process->start();
            #sleep(2);
            
            clearstatcache();
            while ($process->isRunning()) {
                $errorOutput = $process->getErrorOutput();
                if ($errorOutput !== "") {
                    $errorMessage = $this->parseErrorMessage($errorOutput);
                    $result = [
                        'status' => 'error',
                        'experimentID' => $this->experiment->id,
                        'errorMessage' => $errorMessage
                    ];            
                    Cache::put('job-result-' . $this->uniqueId, $result, now()->addMinutes(10));
                }
            }
            
            //call stop.py here?

            Log::channel('server')->error("ERRORMESSAGE: " . $process->getErrorOutput());
            Log::channel('server')->info("PROCESS OUTPUT: " . $process->getOutput());
        } catch (Throwable $e) {
            $errorMessage = $e->getMessage();
            Log::debug("EXCEPTIONLOG: ", [$e->getMessage()]);
        }
    }

    public function failed(Throwable $exception)
    {
        $this->experiment->update([
            'timedout_at' => date("Y-m-d H:i:s")
        ]);
        $this->delete();
    }

    private function parseErrorMessage($errorOutput)
    {
        $errorMessage = '';
    
        if ($this->software === "Cpp") {
            preg_match("/error: '.*?' was not declared in this scope/", $errorOutput, $matches);
            $errorMessage = $matches[0] ?? ltrim(preg_replace('/\s*\/[^:]+:\d+:\d+:\s*/', '; ', $errorOutput), "; ");
        } 
        else if ($this->software === "Python") {
            preg_match('/\n(.+Error:.+)$/', $errorOutput, $matches);
            $errorMessage = $matches[1] ?? 'Error not found';
        } else {
            $errorMessage = 'Unknown error';
        }
    
        return $errorMessage;
    }
}
