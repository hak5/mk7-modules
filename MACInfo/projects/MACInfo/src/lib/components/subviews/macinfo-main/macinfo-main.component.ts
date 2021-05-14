import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../../services/api.service';

@Component({
    selector: 'lib-MACInfo-maininfo',
    templateUrl: './macinfo-main.component.html',
    styleUrls: ['../../MACInfo.component.css', './macinfo-main.component.css']
})
export class MACInfoMainComponent implements OnInit {
    constructor(private API: ApiService) { }

    userInput = '';
    company = '';
    isLoading = false;

    check_mac(): void {
        this.isLoading = true;
        this.API.request({
            module: 'MACInfo',
            action: 'check_mac',
            user_input: this.userInput
        }, (response) => {
            this.isLoading = false;
            this.company = response.company;
        })
    }

    ngOnInit() {
    }
}
