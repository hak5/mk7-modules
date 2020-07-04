import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { SnifferComponent } from './components/Sniffer.component';
import { RouterModule, Routes } from '@angular/router';

import {MaterialModule} from './modules/material/material.module';
import {FlexLayoutModule} from '@angular/flex-layout';

const routes: Routes = [
    { path: '', component: SnifferComponent }
];

@NgModule({
    declarations: [SnifferComponent],
    imports: [
        CommonModule,
        RouterModule.forChild(routes),
        MaterialModule,
        FlexLayoutModule
    ],
    exports: [SnifferComponent]
})
export class SnifferModule { }