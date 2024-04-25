<?php

use App\Http\Controllers\FileController;
//use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Events\DataBroadcaster;

/*
|--------------------------------------------------------------------------
| API Routes
|--------------------------------------------------------------------------
|
| Here is where you can register API routes for your application. These
| routes are loaded by the RouteServiceProvider within a group which
| is assigned the "api" middleware group. Enjoy building your API!
|
*/

//Route::middleware('auth:sanctum')->get('/user', function (Request $request) {
//    return $request->user();
//});

Route::post('/schema/upload', [FileController::class, 'store']);
Route::post('/demo/upload', [FileController::class, 'store']);
Route::get("/experimentDetail/{id}", [FileController::class, 'download']);
// Route::get('/broadcast', function () {
//     for($i = 0; $i <= 10; $i++) {
//         //usleep(10000);
//         broadcast(new DataBroadcaster([rand(0,2)]));
//     }
//     return view('welcome');
// });

