import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { sslsplitComponent } from './components/sslsplit.component';
import { RouterModule, Routes } from '@angular/router';

import {MaterialModule} from './modules/material/material.module';
import {FlexLayoutModule} from '@angular/flex-layout';

import {FormsModule} from '@angular/forms';

const routes: Routes = [
    { path: '', component: sslsplitComponent }
];

@NgModule({
    declarations: [sslsplitComponent],
    imports: [
        CommonModule,
        RouterModule.forChild(routes),
        MaterialModule,
        FlexLayoutModule,
        FormsModule,
    ],
    exports: [sslsplitComponent]
})
export class sslsplitModule { }
