<?php

namespace Database\Seeders;

use App\Models\Software;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;

class SoftwareSeeder extends Seeder
{
    private array $software = [
        'matlab',
        'openloop',
        'openmodelica',
        'scilab',
        'Cpp',
        'Python'
    ];

    /**
     * Run the database seeds.
     *
     * @return void
     */
    public function run()
    {
        foreach($this->software as $soft) {
            DB::table('software')->insert([
                'name' => $soft,
                'created_at' => now(),
                'updated_at' => now()
            ]);
        }
    }
}
