function CoastalContractorExtraction(contractorOptionArray, response) {
  for (let i = 0; i < contractorOptionArray.length; i++) {
    if (contractorOptionArray[i].itemOptionID == response)
      return contractorOptionArray[i].itemOptionText;
  }
  return "Error";
}

// CoastalCoupaWOInstResponses
function CoastalCoupaWOInstResponses(instructions) {
  var description = "";
  var lineCost = 0;
  var contractor = "";
  var capex = true;
  var commodity = "";
  var accSeg6 = "";

  for (let i = 0; i < instructions.length; i++) {
    var instructionName = instructions[i].instruction.replace(
      /<\/?[^>]+(>|$)/g,
      "",
    );
    switch (instructionName) {
      case "Describe the Work that Needs to be Done":
        description = instructions[i].response;
        break;
      case "Is this a Capex Work Order?":
        var options = instructions[i].options;
        let response = GetOptionsResponse(options, instructions[i].response);
        if (response == "Yes") capex = true;
        else capex = false;
        break;
      case "Select the Contractor who will Complete the Work":
        var options = instructions[i].options;
        contractor = GetOptionsResponse(options, instructions[i].response);
        break;
      case "Insert Estimated Dollar Amount for Work (Amount from Quote, if Applicable). NOTE: Set to $500 if Estimate is Less than $500":
        lineCost = instructions[i].response;
        break;
      case "Select Which Type of Capex Work This Is":
        if (instructions[i].response != 0 && instructions[i].response != "") {
          var options = instructions[i].options;
          commodity = GetOptionsResponse(options, instructions[i].response);
          accSeg6 = commodity;
        } else {
          commodity = "Facility Repairs";
          accSeg6 = "Other Operating";
        }
        break;
    }
  }

  return [description, contractor, lineCost, capex, commodity, accSeg6];

  function GetOptionsResponse(options, responseID) {
    for (let k = 0; k < options.length; k++) {
      if (options[k].itemOptionID == responseID)
        return options[k].itemOptionText;
    }
  }
}

// CoastalEHSFormFilter
function CoastalEHSFormFilter(formList, questionSetID) {
  // var filteredForms = [{"rowUID": '', "updateDate": '', "formNumber": '', "businessEntity": ''}];
  var filteredForms = [];
  //var arrCounter = 0;
  var newForm = true;
  //Iterate through each grabbed form
  for (let i = 0; i < formList.length; i++) {
    var form = formList[i].data.Entity;
    if (form.QuestionsSelector == questionSetID) {
      newForm = true;
      //Iterate through each form inserted into the filtered list
      for (let j = 0; j < filteredForms.length; j++) {
        //Check to see if the evaluated inspection is for a different site than in the filteredForms list
        if (form.BusinessEntity == filteredForms[j].BusinessEntity) {
          //Grab only the record of same BusinessEntity that has the most recent UpdatedDtm
          if (
            form.UpdatedDtm > filteredForms[j].UpdateDtm &&
            form.RecurringTaskCompleteDtm &&
            form.RecurringTaskCompleteDtm != ""
          ) {
            //filteredForms[j].updateDate = form.UpdatedDtm;
            //filteredForms[j].rowUID = form.RowUID;
            //filteredForms[j].formNumber = form.FormNumber;
            filteredForms[j] = form;
          }
          newForm = false;
        }
      }
      if (newForm) {
        //filteredForms[arrCounter]={"rowUID": formList[i].RowUID, "updateDate": formList[i].UpdatedDtm, "formNumber": formList[i].FormNumber, "businessEntity": formList[i].BusinessEntity};
        //arrCounter++;
        filteredForms.push(form);
      }
    }
  }
  return filteredForms;
}

// CoastalEHSInspectFormUpdate
function CoastalEHSInspectFormUpdate(inspectionRecord, completionNotes) {
  inspectionRecord.UDFLimbleWOCompletionNotes = completionNotes;
  return inspectionRecord;
}

// CoastalGetChildWONotes
function CoastalGetChildWONotes(childWOs) {
  var childNotes = "";
  //return childWOs[0].body;
  for (let i = 0; i < childWOs.length; i++) {
    var childWOBody = childWOs[i].body;
    //return childWOBody;
    childNotes = childNotes + " " + childWOBody[0].completionNotes;
  }
  return childNotes;
}

// CoastalGetInvoiceInstResponse
function CoastalGetInvoiceInstResponse(instructions) {
  var invoice = { fileName: "", link: "" };
  for (let i = 0; i < instructions.length; i++) {
    if (instructions[i].instruction == "Upload Invoice Here")
      invoice = instructions[i].response[0];
  }

  return invoice;
}

// CoastalSiteManagerExtract
function CoastalSiteManagerExtract(userArr, locationID) {
  var siteManager = { userEmail: "", userName: "" };
  for (let i = 0; i < userArr.length; i++) {
    if (userArr[i].active) {
      var userRoleArr = userArr[i].roles;
      for (let j = 0; j < userRoleArr.length; j++) {
        if (
          userRoleArr[j].name == "View Only" &&
          userRoleArr[j].locationID == locationID &&
          userArr[i].firstName == "Site Manager"
        ) {
          siteManager.userEmail = userArr[i].email;
          siteManager.userName = userArr[i].lastName;
        }
        /*if(userRoleArr[j].name == "View Only" && userRoleArr[j].locationID == locationID){
                    if(userArr[i].lastName.includes("Site Manager")){
                        siteManager.userEmail = userArr[i].email;
                        siteManager.userName = userArr[i].firstName + " " + userArr[i].lastName;
                    }
                }*/
      }
    }
  }
  return siteManager;
}
// EHSLimbleLocationMapping
function EHSLimbleLocationMapping(ehsSite) {
  var splitArr = ehsSite.split(" ");
  var firstName = splitArr[0];
  var limbleName = "";
  var siteNum = firstName.match(/\d+/g);
  if (siteNum && siteNum != "") {
    limbleName = "Coastal " + siteNum;
    if (limbleName == "Coastal 23") {
      if (ehsSite.includes("East Miami Hauling"))
        limbleName = "Coastal 23 - Miami Hauling East";
      else if (ehsSite.includes("Miami East Weld"))
        limbleName = "Coastal 23 - Miami East Weld Shop";
      else limbleName = "Coastal 23 - Miami East Container Yard";
    } else if (limbleName == "Coastal 24") {
      if (ehsSite.includes("Lake Worth"))
        limbleName = "Coastal 24 - Lake Worth Hauling";
      else limbleName = "Coastal 24 - Palm Beach Hauling";
    }
  } else {
    limbleName = ehsSite;
  }

  return limbleName;
}

// LimbleGrabLatestTaskComment
function LimbleGrabLatestTaskComment(commentArr) {
  var maxTimestamp = 0;
  var maxComment = "";

  for (let i = 0; i < commentArr.length; i++) {
    if (commentArr[i].timestamp > maxTimestamp) {
      maxTimestamp = commentArr[i].timestamp;
      maxComment = commentArr[i].comment;
    }
  }
  return maxComment;
}

// NumberToSpelledNumberConverter
function NumberToSpelledNumberConverter(number) {
  //==============================================================
  function numToWords(num = 0) {
    if (num == 0) return "Zero";
    num = ("0".repeat((2 * (num += "").length) % 3) + num).match(/.{3}/g);
    let out = "",
      T10s = [
        "",
        "One",
        "Two",
        "Three",
        "Four",
        "Five",
        "Six",
        "Seven",
        "Eight",
        "Nine",
        "Ten",
        "Eleven",
        "Twelve",
        "Thirteen",
        "Fourteen",
        "Fifteen",
        "Sixteen",
        "Seventeen",
        "Eighteen",
        "Nineteen",
      ],
      T20s = [
        "",
        "",
        "Twenty",
        "Thirty",
        "Forty",
        "Fifty",
        "Sixty",
        "Seventy",
        "Eighty",
        "Ninety",
      ],
      sclT = ["", "Thousand", "Million", "Billion", "Trillion", "Quadrillion"];
    return (
      num.forEach((n, i) => {
        if (+n) {
          let hund = +n[0],
            ten = +n.substring(1),
            scl = sclT[num.length - i - 1];
          out +=
            (out ? " " : "") +
            (hund ? T10s[hund] + " Hundred" : "") +
            (hund && ten ? " " : "") +
            (ten < 20
              ? T10s[ten]
              : T20s[+n[1]] + (+n[2] ? " " : "") + T10s[+n[2]]);
          out += (out && scl ? " " : "") + scl;
        }
      }),
      out
    );
  }
  //==============================================================

  let spelledNum = numToWords(number);
  return spelledNum; //[spelledNum.length-1];
}
