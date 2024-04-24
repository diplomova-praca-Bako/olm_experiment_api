<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;

class DeviceTypeSeeder extends Seeder
{
    private array $device_types = [
        'L3Dcube',
        'L3Dcube FEI',
    ];

    /**
     * Run the database seeds.
     *
     * @return void
     */
    public function run()
    {
        foreach($this->device_types as $device_type) {
            DB::table('device_types')->insert([
                'name' => $device_type,
                'created_at' => now(),
                'updated_at' => now()
            ]);
        }
    }
}